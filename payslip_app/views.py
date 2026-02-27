from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import login as otp_login
from django.utils.crypto import get_random_string
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone as tz
from django.db.models import Q
from axes.decorators import axes_dispatch
from django_ratelimit.decorators import ratelimit
from django.template.loader import get_template
from django.http import FileResponse, Http404
from xhtml2pdf import pisa

from .models import (
    PayslipFile, PayslipRequest, PayslipRetrievalLog,
    EmployeePayslip, AdminAuditLog, PayrollData, audit
)
from .validators import (
    validate_generate_form, validate_request_form,
    validate_reference_number,
)
from .decorators import frontend_admin_required
from .tasks import send_notifications_worker

import csv, os, time
from datetime import datetime


# ─────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────

ALL_MONTHS = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
]
PAGE_SIZE          = 15   # rows per page on dashboard
LOGS_PAGE_SIZE     = 20   # rows per page on retrieval logs


# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def generate_reference():
    return 'PS-' + get_random_string(8, allowed_chars='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')


def get_dashboard_stats():
    stats = cache.get('dashboard_stats')
    if stats is None:
        stats = {
            'total_requests':       PayslipRequest.objects.count(),
            'approved_requests':    PayslipRequest.objects.filter(status='approved').count(),
            'rejected_requests':    PayslipRequest.objects.filter(status='rejected').count(),
            'pending_requests':     PayslipRequest.objects.filter(status='pending').count(),
            'completed_requests':   PayslipRequest.objects.filter(status='completed').count(),
            'uploaded_files_count': PayslipFile.objects.count(),
        }
        cache.set('dashboard_stats', stats, 60)
    return stats


def attach_missing_months(requests_qs):
    """
    Attach missing_months to each request without N+1 queries.
    Fetches all payslip files in one query then maps them in Python.
    """
    ids = [r.pk for r in requests_qs]
    # one query for all uploaded months across these requests
    uploaded_map = {}
    for pf in PayslipFile.objects.filter(request_id__in=ids).values('request_id', 'month'):
        uploaded_map.setdefault(pf['request_id'], []).append(pf['month'])

    for r in requests_qs:
        uploaded = uploaded_map.get(r.pk, [])
        r.missing_months = [m for m in (r.months or []) if m not in uploaded]

    return requests_qs


def paginate(queryset, page_number, per_page=PAGE_SIZE):
    paginator = Paginator(queryset, per_page)
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


# ─────────────────────────────────────────
#  RATE LIMIT ERROR HANDLER
# ─────────────────────────────────────────

def ratelimit_error(request, exception=None):
    return render(request, 'payslip_app/429.html', status=429)


# ─────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────

def home_view(request):
    return render(request, 'payslip_app/home.html')


# ─────────────────────────────────────────
#  ADMIN LOGIN
# ─────────────────────────────────────────

@never_cache
@axes_dispatch
def admin_login_view(request):
    message = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        token    = request.POST.get("otp_token", "").strip()

        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:
            devices = TOTPDevice.objects.filter(user=user, confirmed=True)
            if not devices.exists():
                message = "No 2FA device found. Please set up Google Authenticator."
                audit(request, 'login_failed', target=username, detail="No 2FA device configured")
            else:
                valid_token = False
                for device in devices:
                    if device.verify_token(token):
                        valid_token = True
                        login(request, user)
                        user.otp_device = device
                        audit(request, 'login', target=username, detail="Successful login with 2FA")
                        return redirect('admin_dashboard')
                if not valid_token:
                    message = "Invalid 2FA code."
                    audit(request, 'login_failed', target=username, detail="Wrong 2FA token")
        else:
            message = "Invalid username or password."
            audit(request, 'login_failed', target=username, detail="Invalid credentials")

    return render(request, 'payslip_app/admin_login.html', {'message': message})


# ─────────────────────────────────────────
#  ADMIN LOGOUT
# ─────────────────────────────────────────

@never_cache
@login_required(login_url='/frontend-admin/login/')
@require_POST
def admin_logout_view(request):
    audit(request, 'logout', target=request.user.username)
    logout(request)
    response = redirect('admin_login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma']  = 'no-cache'
    response['Expires'] = '0'
    return response


# ─────────────────────────────────────────
#  ADMIN DASHBOARD  ← pagination + search + date filter + status filter
# ─────────────────────────────────────────

@never_cache
@frontend_admin_required
def admin_dashboard(request):
    qs = PayslipRequest.objects.all().order_by('-created_at')

    # ── SEARCH ──
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(full_name__icontains=search) |
            Q(employee_number__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(department__icontains=search)
        )

    # ── STATUS FILTER ──
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)

    # ── DATE RANGE FILTER ──
    start_date = request.GET.get('start_date', '').strip()
    end_date   = request.GET.get('end_date', '').strip()
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)

    # ── PAGINATION ──
    page     = request.GET.get('page', 1)
    page_obj = paginate(qs, page, PAGE_SIZE)

    # ── ATTACH MISSING MONTHS (no N+1) ──
    attach_missing_months(page_obj.object_list)

    context = {
        'users':         page_obj,
        'page_obj':      page_obj,
        'search':        search,
        'status_filter': status_filter,
        'start_date':    start_date,
        'end_date':      end_date,
        'status_choices': ['pending', 'approved', 'rejected', 'completed', 'in_progress'],
    }
    context.update(get_dashboard_stats())
    return render(request, 'payslip_app/frontend_admin.html', context)


# ─────────────────────────────────────────
#  BULK ACTIONS
# ─────────────────────────────────────────
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

@login_required(login_url='/frontend-admin/login/')
def bulk_action(request):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect('admin_dashboard')

    action = request.POST.get("action")
    selected = request.POST.getlist("selected_ids")

    if not selected:
        messages.error(request, "No requests selected.")
        return redirect('admin_dashboard')

    qs = PayslipRequest.objects.filter(pk__in=selected)
    if not qs.exists():
        messages.error(request, "Selected requests not found.")
        return redirect('admin_dashboard')

    try:
        if action == 'approve':
            count = qs.update(status='approved')
            for req in qs:
                audit(request, 'approve_request', target=req.reference_number, detail="Bulk action")
                if req.email:
                    send_mail(
                        f"Payslip Request {req.reference_number} Approved",
                        f"Hello {req.full_name},\n\nYour payslip request has been approved and is being processed.\n\nRegards,\nMoF Payslip Portal",
                        "no-reply@mof-portal.com",
                        [req.email],
                        fail_silently=False,
                    )
            messages.success(request, f"{count} request(s) approved.")

        elif action == 'reject':
            count = qs.update(status='rejected')
            for req in qs:
                audit(request, 'reject_request', target=req.reference_number, detail="Bulk action")
                if req.email:
                    send_mail(
                        f"Payslip Request {req.reference_number} Rejected",
                        f"Hello {req.full_name},\n\nYour payslip request has been reviewed and unfortunately could not be processed at this time.\n\nPlease contact the ICT Directorate for more information.\n\nRegards,\nMoF Payslip Portal",
                        "no-reply@mof-portal.com",
                        [req.email],
                        fail_silently=False,
                    )
            messages.success(request, f"{count} request(s) rejected.")

        elif action == 'delete':
            refs = list(qs.values_list('reference_number', flat=True))
            count = qs.count()
            qs.delete()
            for ref in refs:
                audit(request, 'delete_request', target=ref, detail="Bulk action")
            messages.success(request, f"{count} request(s) deleted.")

        else:
            messages.error(request, "Unknown action.")
            return redirect('admin_dashboard')

        cache.delete('dashboard_stats')
        return redirect('admin_dashboard')

    except Exception as e:
        messages.error(request, f"Error performing bulk action: {str(e)}")
        return redirect('admin_dashboard') # Only redirect once at the end
# ─────────────────────────────────────────
#  REPORTS
# ─────────────────────────────────────────

@never_cache
@frontend_admin_required
def admin_reports(request):
    audit(request, 'view_logs', detail="Viewed reports page")

    reasons  = PayslipRequest.objects.values_list('reason', flat=True).distinct()
    statuses = ['pending', 'approved', 'rejected', 'completed']
    years    = sorted(PayslipRequest.objects.values_list('year', flat=True).distinct())

    selected_reason = request.GET.get('reason', '')
    selected_status = request.GET.get('status', '')
    selected_year   = request.GET.get('year', '')

    requests_qs = PayslipRequest.objects.all().order_by('-created_at')
    if selected_reason:
        requests_qs = requests_qs.filter(reason=selected_reason)
    if selected_status:
        requests_qs = requests_qs.filter(status=selected_status)
    if selected_year:
        try:
            requests_qs = requests_qs.filter(year=int(selected_year))
        except ValueError:
            pass

    return render(request, 'payslip_app/admin_reports.html', {
        'requests':        requests_qs,
        'reasons':         reasons,
        'statuses':        statuses,
        'years':           years,
        'selected_reason': selected_reason,
        'selected_status': selected_status,
        'selected_year':   selected_year,
        'total_requests':  requests_qs.count(),
    })


# ─────────────────────────────────────────
#  UPLOAD PAYSLIP
# ─────────────────────────────────────────

@never_cache
@frontend_admin_required
def upload_payslip_view(request, request_id):
    if request.method == "POST":
        month = request.POST.get("month", "").strip()
        file  = request.FILES.get("payslip_file")
        req   = get_object_or_404(PayslipRequest, id=request_id)

        if month not in ALL_MONTHS:
            messages.error(request, "Invalid month selected.")
            return redirect("admin_dashboard")

        PayslipFile.objects.create(request=req, month=month, file=file)
        audit(request, 'upload_payslip', target=req.reference_number, detail=f"Uploaded {month}")
        cache.delete('dashboard_stats')

        uploaded_months = list(req.payslip_files.values_list('month', flat=True))
        missing_months  = [m for m in req.months if m not in uploaded_months]

        if not missing_months:
            req.status = "completed"
            req.save()
            if req.email:
                send_mail(
                    f"Your Payslip Request {req.reference_number} is Completed",
                    f"Hello {req.full_name},\n\nAll requested payslips have been uploaded and are ready for download.\n\nUse your reference number {req.reference_number} to access them.\n\nRegards,\nMoF Payslip Portal",
                    "no-reply@mof-portal.com",
                    [req.email],
                    fail_silently=True,
                )
            messages.success(request, f"Payslip uploaded for {month} ✅ All payslips complete.")
        else:
            req.status = "in_progress"
            req.save()
            messages.success(request, f"Uploaded {month}. Remaining: {', '.join(missing_months)}")

    return redirect("admin_dashboard")


# ─────────────────────────────────────────
#  EXPORT REPORTS CSV
# ─────────────────────────────────────────

@never_cache
@frontend_admin_required
def export_reports(request):
    audit(request, 'export_reports')
    reason = request.GET.get("reason")
    status = request.GET.get("status")
    year   = request.GET.get("year")

    requests_qs = PayslipRequest.objects.all()
    if reason:
        requests_qs = requests_qs.filter(reason=reason)
    if status:
        requests_qs = requests_qs.filter(status=status)
    if year:
        requests_qs = requests_qs.filter(year=year)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payslip_requests.csv"'
    writer = csv.writer(response)
    writer.writerow(['Reference', 'Name', 'Employee No.', 'Department', 'Reason', 'Status', 'Year', 'Months', 'Uploaded Months', 'Submitted'])
    for req in requests_qs:
        uploaded = ', '.join(req.payslip_files.values_list('month', flat=True))
        writer.writerow([
            req.reference_number, req.full_name, req.employee_number,
            req.department, req.reason, req.status, req.year,
            ', '.join(req.months or []), uploaded,
            req.created_at.strftime('%Y-%m-%d %H:%M') if req.created_at else '',
        ])
    return response


# ─────────────────────────────────────────
#  EXPORT RETRIEVAL LOGS CSV  ← new
# ─────────────────────────────────────────

@never_cache
@frontend_admin_required
def export_retrieval_logs(request):
    audit(request, 'export_reports', detail="Exported retrieval logs CSV")

    logs = PayslipRetrievalLog.objects.all().order_by('-request_time')

    # Apply same filters as the logs page so export respects current filter
    ministry   = request.GET.get('ministry', '').strip()
    start_date = request.GET.get('start_date', '')
    end_date   = request.GET.get('end_date', '')
    month      = request.GET.get('month', '')

    if ministry:
        logs = logs.filter(ministry__icontains=ministry)
    if start_date:
        logs = logs.filter(request_time__date__gte=start_date)
    if end_date:
        logs = logs.filter(request_time__date__lte=end_date)
    if month:
        logs = logs.filter(months__icontains=month)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="retrieval_logs.csv"'
    writer = csv.writer(response)
    writer.writerow(['Time', 'Full Name', 'Pincode', 'DOB', 'Department', 'Ministry', 'Year', 'Months', 'IP Address'])
    for log in logs:
        writer.writerow([
            log.request_time.strftime('%Y-%m-%d %H:%M') if log.request_time else '',
            log.full_name, log.pincode,
            log.dob.strftime('%Y-%m-%d') if log.dob else '',
            log.department, log.ministry, log.year,
            log.months, log.ip_address,
        ])
    return response


# ─────────────────────────────────────────
#  APPROVE / REJECT / DELETE / MARK COMPLETED (single)
# ─────────────────────────────────────────

@never_cache
@frontend_admin_required
def approve_request(request, pk):
    req = get_object_or_404(PayslipRequest, pk=pk)
    req.status = 'approved'
    req.save()
    cache.delete('dashboard_stats')
    audit(request, 'approve_request', target=req.reference_number)
    if req.email:
        send_mail(
            f"Payslip Request {req.reference_number} Approved",
            f"Hello {req.full_name},\n\nYour payslip request has been approved and is being processed.\n\nRegards,\nMoF Payslip Portal",
            "no-reply@mof-portal.com",
            [req.email],
            fail_silently=True,
        )
    messages.success(request, "Request approved!")
    return redirect('admin_dashboard')


@never_cache
@frontend_admin_required
def reject_request(request, pk):
    req = get_object_or_404(PayslipRequest, pk=pk)
    req.status = 'rejected'
    req.save()
    cache.delete('dashboard_stats')
    audit(request, 'reject_request', target=req.reference_number)
    if req.email:
        send_mail(
            f"Payslip Request {req.reference_number} Rejected",
            f"Hello {req.full_name},\n\nYour payslip request has been reviewed and unfortunately could not be processed at this time. Please contact the ICT Directorate for more information.\n\nRegards,\nMoF Payslip Portal",
            "no-reply@mof-portal.com",
            [req.email],
            fail_silently=True,
        )
    messages.success(request, "Request rejected!")
    return redirect('admin_dashboard')


@never_cache
@frontend_admin_required
def delete_request(request, pk):
    req = get_object_or_404(PayslipRequest, pk=pk)
    ref = req.reference_number
    req.delete()
    cache.delete('dashboard_stats')
    audit(request, 'delete_request', target=ref)
    messages.success(request, "Request deleted!")
    return redirect('admin_dashboard')


@never_cache
@frontend_admin_required
def mark_completed(request, pk):
    req = get_object_or_404(PayslipRequest, pk=pk)
    if not req.payslip_files.exists():
        messages.error(request, "Upload payslip files before marking complete.")
        return redirect('admin_dashboard')
    req.status = 'completed'
    req.save()
    cache.delete('dashboard_stats')
    audit(request, 'mark_completed', target=req.reference_number)
    messages.success(request, "Request marked as completed.")
    return redirect('admin_dashboard')


# ─────────────────────────────────────────
#  EMPLOYEE REQUEST FORM
# ─────────────────────────────────────────

@never_cache
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def request_form_view(request):
    years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    success, reference_number, error = False, None, None

    if request.method == "POST":
        cleaned, errors = validate_request_form(request.POST)
        if errors:
            error = " | ".join(errors.values())
        else:
            try:
                ref = generate_reference()
                PayslipRequest.objects.create(
                    full_name        = cleaned['full_name'],
                    employee_number  = cleaned['employee_pincode'],
                    department       = cleaned['department'],
                    job_title        = cleaned['job_title'],
                    phone_number     = cleaned['phone_number'],
                    email            = request.POST.get('email', '').strip()[:254],
                    months           = cleaned['months'],
                    year             = cleaned['year'],
                    id_card_front    = request.FILES.get('id_card_front'),
                    id_card_back     = request.FILES.get('id_card_back'),
                    reference_number = ref,
                    reason           = cleaned['reason'],
                    status           = 'pending',
                )
                success, reference_number = True, ref
                cache.delete('dashboard_stats')
            except Exception:
                error = "Submission failed. Please try again."

    return render(request, "payslip_app/request_form.html", {
        'months': ALL_MONTHS, 'years': years,
        'success': success, 'reference_number': reference_number, 'error': error,
    })


# ─────────────────────────────────────────
#  CHECK PAYSLIP STATUS
# ─────────────────────────────────────────

@never_cache
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def check_payslip_view(request):
    context = {}
    if request.method == "POST":
        ref_number = request.POST.get("ref_number", "").strip()
        try:
            ref_number = validate_reference_number(ref_number)
        except Exception:
            context["error"] = "Invalid reference number format. Expected: PS-XXXXXXXX"
            return render(request, "payslip_app/check_payslip.html", context)

        try:
            req = PayslipRequest.objects.get(reference_number=ref_number)
            uploaded_months  = list(req.payslip_files.values_list('month', flat=True))
            missing_months   = [m for m in (req.months or []) if m not in uploaded_months]
            context["req"]            = req
            context["uploaded_months"] = uploaded_months
            context["missing_months"]  = missing_months
            if req.payslip_files.exists():
                context["success"] = True
            else:
                context["message"] = "Your request was found but payslips have not been uploaded yet."
        except PayslipRequest.DoesNotExist:
            context["error"] = "Invalid reference number. Please check and try again."

    return render(request, "payslip_app/check_payslip.html", context)


# ─────────────────────────────────────────
#  GENERATE PAYSLIP
# ─────────────────────────────────────────

@never_cache
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def generate_payslip_view(request):
    years = list(
        EmployeePayslip.objects.using('mock_payslips')
        .values_list('year', flat=True).distinct().order_by('year')
    )
    context = {'months': ALL_MONTHS, 'years': years}

    if request.method == 'POST':
        ip = get_client_ip(request)
        cleaned, errors = validate_generate_form(request.POST)
        if errors:
            context['error'] = " | ".join(errors.values())
            return render(request, 'payslip_app/generate_form.html', context)

        pin_code        = cleaned['pin_code']
        nin             = cleaned['nin']
        selected_months = cleaned['months']
        year            = cleaned['year']

        payslips = EmployeePayslip.objects.using('mock_payslips').filter(
            pin_code=pin_code, nin=nin, month__in=selected_months, year=year
        ).order_by('month')

        if not payslips.exists():
            context['error'] = "No payslips found. Please check your entered details."
            PayslipRetrievalLog.objects.create(
                full_name='UNKNOWN', pincode=pin_code, dob=None,
                department='UNKNOWN', ministry='UNKNOWN',
                months=','.join(selected_months), year=year,
                ip_address=ip, request_time=datetime.now(),
            )
            return render(request, 'payslip_app/generate_form.html', context)

        for p in payslips:
            p.net_salary = (p.salary or 0) + (p.allowances or 0) - (p.deductions or 0)

        emp = payslips.first()
        PayslipRetrievalLog.objects.create(
            full_name=emp.full_name, pincode=pin_code, dob=emp.dob,
            department=emp.department, ministry=emp.ministry,
            months=','.join(selected_months), year=year,
            ip_address=ip, request_time=datetime.now(),
        )

        pdf_context = {
            'full_name': emp.full_name, 'pin_code': emp.pin_code,
            'nin': emp.nin, 'department': emp.department,
            'ministry': emp.ministry, 'dob': emp.dob,
            'year': year, 'months': payslips, 'request_time': datetime.now(),
        }
        template    = get_template('payslip_app/payslip_template.html')
        html        = template.render(pdf_context)
        response    = HttpResponse(content_type='application/pdf')
        filename    = f"{emp.full_name}_payslips_{year}_{int(time.time())}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma']  = 'no-cache'
        response['Expires'] = '0'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generating PDF')
        return response

    return render(request, 'payslip_app/generate_form.html', context)


# ─────────────────────────────────────────
#  RETRIEVAL LOGS  ← pagination + CSV export
# ─────────────────────────────────────────

@never_cache
@frontend_admin_required
def retrieval_logs_view(request):
    audit(request, 'view_logs', detail="Viewed retrieval logs")

    logs = PayslipRetrievalLog.objects.all().order_by('-request_time')

    ministry   = request.GET.get('ministry', '').strip()
    start_date = request.GET.get('start_date', '')
    end_date   = request.GET.get('end_date', '')
    month      = request.GET.get('month', '')

    if ministry:
        logs = logs.filter(ministry__icontains=ministry)
    if start_date:
        logs = logs.filter(request_time__date__gte=start_date)
    if end_date:
        logs = logs.filter(request_time__date__lte=end_date)
    if month:
        logs = logs.filter(months__icontains=month)

    page     = request.GET.get('page', 1)
    page_obj = paginate(logs, page, LOGS_PAGE_SIZE)

    return render(request, 'payslip_app/admin_retrieval_logs.html', {
        'logs':                page_obj,
        'page_obj':            page_obj,
        'selected_ministry':   ministry,
        'selected_start_date': start_date,
        'selected_end_date':   end_date,
        'selected_month':      month,
        'total_logs':          logs.count(),
    })


@never_cache
@frontend_admin_required
def delete_retrieval_log(request, pk):
    log = get_object_or_404(PayslipRetrievalLog, pk=pk)
    audit(request, 'delete_log', target=f"Log #{pk} — {log.full_name}", detail=f"IP: {log.ip_address}")
    log.delete()
    messages.success(request, "Retrieval log deleted.")
    return redirect('retrieval_logs')


# ─────────────────────────────────────────
#  DOWNLOAD PAYSLIP
# ─────────────────────────────────────────

def download_payslip_view(request, file_id):
    payslip   = get_object_or_404(PayslipFile, id=file_id)
    file_path = payslip.file.path
    if not os.path.exists(file_path):
        raise Http404("File not found")
    response = FileResponse(open(file_path, "rb"), as_attachment=True)
    response["Content-Type"]        = "application/pdf"
    response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response


# ─────────────────────────────────────────
#  NOTIFICATIONS
# ─────────────────────────────────────────

@never_cache
@frontend_admin_required
def admin_notifications_view(request):
    new_payrolls = PayrollData.objects.filter(notified=False)

    if request.method == 'POST':
        batch_size = 20
        total      = new_payrolls.count()
        sent_count = 0
        messages_sent = []

        for payroll in new_payrolls[:batch_size]:
            msg = (
                f"Hello {payroll.full_name}, your payslip for "
                f"{payroll.month} {payroll.year} is available. "
                f"Reference Code: {payroll.reference_code}"
            )
            messages_sent.append(msg)
            payroll.notified = True
            payroll.save()
            sent_count += 1

        audit(request, 'view_logs', detail=f"Sent {sent_count} notifications, {total - sent_count} remaining")
        return JsonResponse({'sent': sent_count, 'remaining': total - sent_count, 'messages': messages_sent})

    return render(request, "payslip_app/admin_notifications.html", {'new_payrolls': new_payrolls})


@never_cache
@frontend_admin_required
def send_notifications_view(request):
    if request.method == 'POST':
        send_notifications_worker.delay()
        audit(request, 'view_logs', detail="Queued notification batch via Celery")
        return render(request, 'notifications_sent.html', {'count': "Queued in Celery"})
    pending_payslips = PayrollData.objects.filter(notified=False)
    return render(request, 'send_notifications.html', {'pending_payslips': pending_payslips})


# ─────────────────────────────────────────
#  AUDIT LOGS
# ─────────────────────────────────────────

# Replace your existing admin_audit_logs_view in views.py with this:

@never_cache
@frontend_admin_required
def admin_audit_logs_view(request):
    logs = AdminAuditLog.objects.select_related('admin').order_by('-timestamp')

    # ── FILTERS ──
    selected_admin      = request.GET.get('admin', '').strip()
    selected_action     = request.GET.get('action', '').strip()
    selected_start_date = request.GET.get('start_date', '').strip()
    selected_end_date   = request.GET.get('end_date', '').strip()

    if selected_admin:
        logs = logs.filter(admin__username__icontains=selected_admin)
    if selected_action:
        logs = logs.filter(action=selected_action)
    if selected_start_date:
        logs = logs.filter(timestamp__date__gte=selected_start_date)
    if selected_end_date:
        logs = logs.filter(timestamp__date__lte=selected_end_date)

    # ── PAGINATION ── 25 rows per page
    page     = request.GET.get('page', 1)
    page_obj = paginate(logs, page, 25)

    # ── STATS ──
    today = tz.localdate()
    return render(request, 'payslip_app/admin_audit_logs.html', {
        'logs':                page_obj,        # paginated — template iterates this
        'page_obj':            page_obj,        # for pagination controls
        'total_logins':        AdminAuditLog.objects.filter(action='login').count(),
        'total_failures':      AdminAuditLog.objects.filter(action='login_failed').count(),
        'total_actions':       AdminAuditLog.objects.exclude(
                                   action__in=['login', 'logout', 'login_failed', 'view_logs']
                               ).count(),
        'today_count':         AdminAuditLog.objects.filter(timestamp__date=today).count(),
        'selected_admin':      selected_admin,
        'selected_action':     selected_action,
        'selected_start_date': selected_start_date,
        'selected_end_date':   selected_end_date,
    })
    