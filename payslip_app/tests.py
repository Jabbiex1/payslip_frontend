import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import PayslipDownloadLog, PayslipFile, PayslipRequest, PayslipRetrievalLog
from .views import DOWNLOAD_TOKEN_SALT


class BaseMediaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._temp_media = tempfile.mkdtemp(prefix="payslip_test_media_")
        cls._override = override_settings(MEDIA_ROOT=cls._temp_media, USE_X_ACCEL_REDIRECT=False)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        shutil.rmtree(cls._temp_media, ignore_errors=True)
        super().tearDownClass()


class DownloadSecurityTests(BaseMediaTestCase):
    def setUp(self):
        self.request_obj = PayslipRequest.objects.create(
            full_name="Test User",
            employee_number="10001",
            department="ICT",
            job_title="Officer",
            phone_number="+23276000000",
            email="test@example.com",
            reason="Bank request",
            year=2025,
            months=["January"],
            status="completed",
            reference_number="PS-AB12CD34",
        )
        self.payslip_file = PayslipFile.objects.create(
            request=self.request_obj,
            month="January",
            file=SimpleUploadedFile(
                "january.pdf",
                b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF",
                content_type="application/pdf",
            ),
        )

    def _token_for_client(self, client):
        session = client.session
        session["checked_ref"] = self.request_obj.reference_number
        session.save()
        return signing.dumps(
            {
                "file_id": self.payslip_file.id,
                "request_id": self.request_obj.id,
                "reference_number": self.request_obj.reference_number,
                "session_key": session.session_key,
            },
            salt=DOWNLOAD_TOKEN_SALT,
        )

    def test_download_requires_token_for_public_user(self):
        response = self.client.get(reverse("download_payslip", args=[self.payslip_file.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(PayslipDownloadLog.objects.filter(status="blocked", reason="missing_token").exists())

    def test_download_accepts_valid_token(self):
        token = self._token_for_client(self.client)
        response = self.client.get(reverse("download_payslip", args=[self.payslip_file.id]), {"token": token})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PayslipDownloadLog.objects.filter(status="success").exists())

    def test_download_rejects_token_with_session_mismatch(self):
        other_client = Client()
        mismatched_token = self._token_for_client(other_client)
        session = self.client.session
        session["checked_ref"] = self.request_obj.reference_number
        session.save()
        response = self.client.get(
            reverse("download_payslip", args=[self.payslip_file.id]),
            {"token": mismatched_token},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(PayslipDownloadLog.objects.filter(status="blocked", reason="token_mismatch").exists())

    def test_staff_admin_can_download_without_token(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="admin1", password="pass12345", is_staff=True)
        self.client.force_login(admin)
        response = self.client.get(reverse("download_payslip", args=[self.payslip_file.id]))
        self.assertEqual(response.status_code, 200)


class PostOnlyEndpointTests(BaseMediaTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(username="staff1", password="pass12345", is_staff=True)
        self.client.force_login(self.admin)

        self.request_obj = PayslipRequest.objects.create(
            full_name="Test User",
            employee_number="10002",
            department="ICT",
            job_title="Officer",
            phone_number="+23277000000",
            email="test2@example.com",
            reason="Bank request",
            year=2025,
            months=["January"],
            status="pending",
            reference_number="PS-EF56GH78",
        )
        self.retrieval_log = PayslipRetrievalLog.objects.create(
            full_name="Test User",
            pincode="10002",
            dob=None,
            department="ICT",
            ministry="Finance",
            months="January",
            year=2025,
            ip_address="127.0.0.1",
            request_time=timezone.now(),
        )

    def test_state_changing_endpoints_are_post_only(self):
        urls = [
            reverse("bulk_action"),
            reverse("upload_payslip", args=[self.request_obj.id]),
            reverse("approve_request", args=[self.request_obj.id]),
            reverse("reject_request", args=[self.request_obj.id]),
            reverse("delete_request", args=[self.request_obj.id]),
            reverse("mark_completed", args=[self.request_obj.id]),
            reverse("delete_retrieval_log", args=[self.retrieval_log.id]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 405, msg=f"Expected 405 for GET {url}")


class UploadValidationTests(BaseMediaTestCase):
    def test_request_form_rejects_invalid_id_upload(self):
        response = self.client.post(
            reverse("request_form"),
            {
                "full_name": "Fatima Conteh",
                "employee_pincode": "10045",
                "department": "Ministry of Health",
                "job_title": "Senior Accountant",
                "phone_number": "+23276000000",
                "email": "fatima@example.com",
                "reason": "Loan application",
                "months": ["January"],
                "year": "2025",
                "id_card_front": SimpleUploadedFile(
                    "front.exe",
                    b"MZ....",
                    content_type="application/octet-stream",
                ),
                "id_card_back": SimpleUploadedFile(
                    "back.png",
                    b"\x89PNG\r\n\x1a\nvalidpng",
                    content_type="image/png",
                ),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ID card front")
        self.assertEqual(PayslipRequest.objects.count(), 0)

    def test_upload_payslip_rejects_non_pdf(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="staff2", password="pass12345", is_staff=True)
        self.client.force_login(admin)

        request_obj = PayslipRequest.objects.create(
            full_name="Upload User",
            employee_number="10003",
            department="ICT",
            job_title="Officer",
            phone_number="+23278000000",
            email="upload@example.com",
            reason="Testing",
            year=2025,
            months=["January"],
            status="pending",
            reference_number="PS-IJ90KL12",
        )

        response = self.client.post(
            reverse("upload_payslip", args=[request_obj.id]),
            {
                "month": "January",
                "payslip_file": SimpleUploadedFile(
                    "note.txt",
                    b"not a pdf",
                    content_type="text/plain",
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PayslipFile.objects.filter(request=request_obj).count(), 0)

    def test_upload_payslip_accepts_valid_pdf(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="staff3", password="pass12345", is_staff=True)
        self.client.force_login(admin)

        request_obj = PayslipRequest.objects.create(
            full_name="Upload User 2",
            employee_number="10004",
            department="ICT",
            job_title="Officer",
            phone_number="+23279000000",
            email="upload2@example.com",
            reason="Testing",
            year=2025,
            months=["January"],
            status="pending",
            reference_number="PS-MN34OP56",
        )

        response = self.client.post(
            reverse("upload_payslip", args=[request_obj.id]),
            {
                "month": "January",
                "payslip_file": SimpleUploadedFile(
                    "jan.pdf",
                    b"%PDF-1.4\ncontent\n%%EOF",
                    content_type="application/pdf",
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PayslipFile.objects.filter(request=request_obj).count(), 1)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, "completed")
