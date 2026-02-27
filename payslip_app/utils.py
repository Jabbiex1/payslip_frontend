from django.core.mail import send_mail
from django.conf import settings

def send_payslip_ready_email(payslip_request):
    if not payslip_request.email:
        return

    subject = "Your Payslips Are Ready"
    message = f"""
Dear {payslip_request.full_name},

Your requested payslips for year {payslip_request.year} have now been uploaded.

Reference Number: {payslip_request.reference_number}

You can now visit the portal and download them.

Regards,
MoF Payslip Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [payslip_request.email],
        fail_silently=False
    )
# payslip_app/utils.py
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
from .models import PayslipRetrievalLog
from datetime import datetime

def log_payslip_attempt(full_name, pin_code, dob, months, year, ip_address, department=None, ministry=None):
    """
    Logs a payslip retrieval attempt.
    - full_name: Name of the employee or 'UNKNOWN' if not found
    - pin_code: Employee PIN code
    - dob: Employee date of birth
    - months: List of months requested
    - year: Year requested
    - ip_address: Request IP
    - department: Optional employee department
    - ministry: Optional employee ministry
    """
    try:
        PayslipRetrievalLog.objects.create(
            full_name=full_name,
            pin_code=pin_code,
            dob=dob,
            months=", ".join(months),
            year=year,
            ip_address=ip_address,
            department=department,
            ministry=ministry,
            requested_at=datetime.now()
        )
    except Exception as e:
        # Optional: just print/log to console if DB fails
        print(f"Failed to log payslip attempt: {e}")