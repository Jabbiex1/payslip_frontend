# payslip_app/tasks.py
import time
from celery import shared_task
from .models import PayrollData, NotificationLog
from .services.payroll_service import fetch_payslips_for_notification

# Placeholder for SMS API
def send_sms(phone, message):
    print(f"FAKE SEND -> {phone}: {message}")
    return {"status": "success"}  # simulate API response

# Batch worker for multiple notifications
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries':3})
def send_notifications_worker(self):
    pending_payslips = fetch_payslips_for_notification(limit=1000)
    sent_count = 0

    for payslip in pending_payslips:
        phone = payslip.phone_number
        message = f"Hello {payslip.full_name}, your payslip {payslip.reference_code} is available."

        try:
            result = send_sms(phone, message)
            if result.get("status") == "success":
                NotificationLog.objects.create(
                    staff_number=payslip.staff_number,
                    reference_code=payslip.reference_code,
                    status="sent"
                )
                payslip.notified = True
                payslip.save()
                sent_count += 1
            else:
                NotificationLog.objects.create(
                    staff_number=payslip.staff_number,
                    reference_code=payslip.reference_code,
                    status="failed"
                )
        except Exception as e:
            NotificationLog.objects.create(
                staff_number=payslip.staff_number,
                reference_code=payslip.reference_code,
                status="error"
            )

        # throttle ~1000/sec
        time.sleep(0.001)

    return sent_count

# Single notification task
@shared_task
def send_notification(payroll_id):
    payroll = PayrollData.objects.get(id=payroll_id)
    print(f"Sending notification for {payroll.full_name}")
    NotificationLog.objects.create(
        staff_number=payroll.staff_number,
        reference_code=payroll.reference_code,
        status="sent"
    )
    payroll.notified = True
    payroll.save()