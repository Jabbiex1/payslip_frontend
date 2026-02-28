from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("payslip_app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PayslipDownloadLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_reference", models.CharField(blank=True, db_index=True, max_length=50)),
                ("month", models.CharField(blank=True, max_length=20)),
                (
                    "status",
                    models.CharField(
                        choices=[("success", "Success"), ("blocked", "Blocked"), ("missing", "Missing")],
                        default="success",
                        max_length=20,
                    ),
                ),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("session_key", models.CharField(blank=True, max_length=64)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                (
                    "payslip_file",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="download_logs",
                        to="payslip_app.payslipfile",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-requested_at"],
            },
        ),
    ]
