from django.contrib.auth.models import User
from django.db import models


class PayslipRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
    ]

    full_name = models.CharField(max_length=200)
    employee_number = models.CharField(max_length=50)
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    reason = models.TextField()
    year = models.IntegerField()
    months = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reference_number = models.CharField(max_length=50, unique=True)
    id_card_front = models.ImageField(upload_to="id_cards/", null=True, blank=True)
    id_card_back = models.ImageField(upload_to="id_cards/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.reference_number}"


class PayslipFile(models.Model):
    request = models.ForeignKey(PayslipRequest, on_delete=models.CASCADE, related_name="payslip_files")
    month = models.CharField(max_length=20)
    file = models.FileField(upload_to="payslips/")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class PayslipRetrievalLog(models.Model):
    full_name = models.CharField(max_length=255)
    pincode = models.CharField(max_length=50)
    dob = models.DateField(null=True, blank=True)
    department = models.CharField(max_length=255)
    ministry = models.CharField(max_length=255)
    months = models.CharField(max_length=255)
    year = models.IntegerField()
    ip_address = models.GenericIPAddressField()
    request_time = models.DateTimeField()


class PayrollData(models.Model):
    staff_number = models.CharField(max_length=50)
    full_name = models.CharField(max_length=100)
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    pin_code = models.CharField(max_length=10)
    dob = models.DateField(default="2000-01-01")
    notified = models.BooleanField(default=False)
    reference_code = models.CharField(max_length=50, blank=True, null=True)


class NotificationLog(models.Model):
    staff_number = models.CharField(max_length=50)
    reference_code = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)


class EmployeePayslip(models.Model):
    full_name = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=20)
    nin = models.CharField(max_length=50)
    department = models.CharField(max_length=100)
    ministry = models.CharField(max_length=100)
    dob = models.DateField()
    job_title = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2)
    deductions = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.CharField(max_length=20)
    year = models.IntegerField()

    class Meta:
        db_table = "employee_payslip"
        unique_together = ("nin", "month", "year")


class AdminAuditLog(models.Model):
    ACTION_CHOICES = [
        ("login", "Admin Login"),
        ("logout", "Admin Logout"),
        ("login_failed", "Failed Login Attempt"),
        ("approve_request", "Approved Request"),
        ("reject_request", "Rejected Request"),
        ("delete_request", "Deleted Request"),
        ("upload_payslip", "Uploaded Payslip"),
        ("mark_completed", "Marked Completed"),
        ("delete_log", "Deleted Retrieval Log"),
        ("view_logs", "Viewed Retrieval Logs"),
        ("export_reports", "Exported Reports"),
    ]

    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target = models.CharField(max_length=255, blank=True, null=True)
    detail = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payslip_app_adminauditlog"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.admin} - {self.action} - {self.timestamp}"


class PayslipDownloadLog(models.Model):
    STATUS_CHOICES = [
        ("success", "Success"),
        ("blocked", "Blocked"),
        ("missing", "Missing"),
    ]

    payslip_file = models.ForeignKey(
        PayslipFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="download_logs",
    )
    request_reference = models.CharField(max_length=50, blank=True, db_index=True)
    month = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="success")
    reason = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    session_key = models.CharField(max_length=64, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.request_reference} - {self.status} - {self.requested_at}"


def audit(request, action: str, target: str = None, detail: str = None):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
    AdminAuditLog.objects.create(
        admin=request.user if request.user.is_authenticated else None,
        action=action,
        target=target,
        detail=detail,
        ip_address=ip or None,
    )
