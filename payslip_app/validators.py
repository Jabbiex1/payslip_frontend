import os
import re
from django import forms
from django.utils.text import get_valid_filename


# ─────────────────────────────────────────
#  REGEX PATTERNS
# ─────────────────────────────────────────
PIN_CODE_RE    = re.compile(r'^\d{3,10}$')
NIN_RE         = re.compile(r'^[A-Za-z0-9\-]{4,20}$')
PHONE_RE       = re.compile(r'^\+?[\d\s\-]{7,20}$')
NAME_RE        = re.compile(r"^[A-Za-z\s'\-\.]{2,100}$")
REF_NUMBER_RE  = re.compile(r'^PS-[A-Za-z0-9]{8}$')
YEAR_MIN       = 2015
YEAR_MAX       = 2030

VALID_MONTHS = {
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
}

MAX_ID_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PAYSLIP_UPLOAD_BYTES = 15 * 1024 * 1024

ALLOWED_ID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
ALLOWED_ID_CONTENT_TYPES = {'image/jpeg', 'image/png', 'application/pdf'}
ALLOWED_PAYSLIP_CONTENT_TYPES = {'application/pdf'}


# ─────────────────────────────────────────
#  INDIVIDUAL FIELD VALIDATORS
# ─────────────────────────────────────────

def validate_pin_code(value: str) -> str:
    value = value.strip()
    if not PIN_CODE_RE.match(value):
        raise forms.ValidationError(
            "PIN code must be 3–10 digits only."
        )
    return value


def validate_nin(value: str) -> str:
    value = value.strip().upper()
    if not NIN_RE.match(value):
        raise forms.ValidationError(
            "NIN must be 4–20 alphanumeric characters."
        )
    return value


def validate_full_name(value: str) -> str:
    value = value.strip()
    if not NAME_RE.match(value):
        raise forms.ValidationError(
            "Name must be 2–100 characters and contain letters only."
        )
    return value


def validate_phone_number(value: str) -> str:
    value = value.strip()
    if not PHONE_RE.match(value):
        raise forms.ValidationError(
            "Enter a valid phone number (7–20 digits, optional +/spaces/dashes)."
        )
    return value


def validate_months(months: list) -> list:
    if not months:
        raise forms.ValidationError("At least one month must be selected.")
    invalid = [m for m in months if m not in VALID_MONTHS]
    if invalid:
        raise forms.ValidationError(f"Invalid month(s): {', '.join(invalid)}")
    return months


def validate_year(value) -> int:
    try:
        year = int(value)
    except (ValueError, TypeError):
        raise forms.ValidationError("Invalid year.")
    if not YEAR_MIN <= year <= YEAR_MAX:
        raise forms.ValidationError(
            f"Year must be between {YEAR_MIN} and {YEAR_MAX}."
        )
    return year


def validate_reference_number(value: str) -> str:
    value = value.strip().upper()
    if not REF_NUMBER_RE.match(value):
        raise forms.ValidationError(
            "Reference number must be in the format PS-XXXXXXXX."
        )
    return value


def validate_department(value: str) -> str:
    value = value.strip()
    if len(value) < 2 or len(value) > 150:
        raise forms.ValidationError(
            "Department name must be 2–150 characters."
        )
    # Strip any HTML/script tags
    if re.search(r'<[^>]+>', value):
        raise forms.ValidationError("Invalid characters in department name.")
    return value


def validate_ministry(value: str) -> str:
    value = value.strip()
    if len(value) < 2 or len(value) > 150:
        raise forms.ValidationError(
            "Ministry name must be 2–150 characters."
        )
    if re.search(r'<[^>]+>', value):
        raise forms.ValidationError("Invalid characters in ministry name.")
    return value


def validate_reason(value: str) -> str:
    value = value.strip()
    if len(value) < 5 or len(value) > 500:
        raise forms.ValidationError(
            "Reason must be 5–500 characters."
        )
    if re.search(r'<[^>]+>', value):
        raise forms.ValidationError("Invalid characters in reason field.")
    return value


def _peek_head(uploaded_file, size: int = 16) -> bytes:
    position = uploaded_file.tell()
    head = uploaded_file.read(size)
    uploaded_file.seek(position)
    return head


def _sanitize_uploaded_name(uploaded_file, default_prefix: str) -> None:
    original = os.path.basename(uploaded_file.name or "")
    stem, ext = os.path.splitext(original)
    stem = get_valid_filename(stem)[:80] or default_prefix
    uploaded_file.name = f"{stem}{ext.lower()}"


def validate_id_upload(uploaded_file, field_label: str) -> None:
    if not uploaded_file:
        raise forms.ValidationError(f"{field_label} is required.")
    if uploaded_file.size > MAX_ID_UPLOAD_BYTES:
        raise forms.ValidationError(f"{field_label} exceeds 5MB.")

    ext = os.path.splitext(uploaded_file.name or "")[1].lower()
    if ext not in ALLOWED_ID_EXTENSIONS:
        raise forms.ValidationError(f"{field_label} must be JPG, PNG, or PDF.")

    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type not in ALLOWED_ID_CONTENT_TYPES:
        raise forms.ValidationError(f"{field_label} has an invalid content type.")

    head = _peek_head(uploaded_file, 16)
    if ext in {".jpg", ".jpeg"} and not head.startswith(b"\xff\xd8\xff"):
        raise forms.ValidationError(f"{field_label} is not a valid JPEG.")
    if ext == ".png" and not head.startswith(b"\x89PNG\r\n\x1a\n"):
        raise forms.ValidationError(f"{field_label} is not a valid PNG.")
    if ext == ".pdf" and not head.startswith(b"%PDF"):
        raise forms.ValidationError(f"{field_label} is not a valid PDF.")

    _sanitize_uploaded_name(uploaded_file, "id_card")


def validate_payslip_pdf_upload(uploaded_file) -> None:
    if not uploaded_file:
        raise forms.ValidationError("Please attach a payslip PDF file.")
    if uploaded_file.size > MAX_PAYSLIP_UPLOAD_BYTES:
        raise forms.ValidationError("Payslip file exceeds 15MB.")

    ext = os.path.splitext(uploaded_file.name or "")[1].lower()
    if ext != ".pdf":
        raise forms.ValidationError("Payslip file must be a PDF.")

    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type not in ALLOWED_PAYSLIP_CONTENT_TYPES:
        raise forms.ValidationError("Payslip file has an invalid content type.")

    if not _peek_head(uploaded_file, 4).startswith(b"%PDF"):
        raise forms.ValidationError("Payslip file is not a valid PDF.")

    _sanitize_uploaded_name(uploaded_file, "payslip")


# ─────────────────────────────────────────
#  CONVENIENCE: validate a whole POST dict
#  Returns (cleaned_data, errors_dict)
# ─────────────────────────────────────────

def validate_generate_form(post_data: dict) -> tuple[dict, dict]:
    cleaned = {}
    errors  = {}

    fields = {
        'full_name':  validate_full_name,
        'pin_code':   validate_pin_code,
        'nin':        validate_nin,
        'department': validate_department,
        'ministry':   validate_ministry,
    }

    for field, validator in fields.items():
        value = post_data.get(field, '')
        try:
            cleaned[field] = validator(value)
        except forms.ValidationError as e:
            errors[field] = e.message

    # Year
    try:
        cleaned['year'] = validate_year(post_data.get('year'))
    except forms.ValidationError as e:
        errors['year'] = e.message

    # Months
    try:
        cleaned['months'] = validate_months(post_data.getlist('months'))
    except forms.ValidationError as e:
        errors['months'] = e.message

    return cleaned, errors


def validate_request_form(post_data: dict) -> tuple[dict, dict]:
    cleaned = {}
    errors  = {}

    fields = {
        'full_name':        validate_full_name,
        'employee_pincode': validate_pin_code,
        'department':       validate_department,
        'phone_number':     validate_phone_number,
        'reason':           validate_reason,
    }

    for field, validator in fields.items():
        value = post_data.get(field, '')
        try:
            cleaned[field] = validator(value)
        except forms.ValidationError as e:
            errors[field] = e.message

    # Job title — basic length check
    job_title = post_data.get('job_title', '').strip()
    if len(job_title) < 2 or len(job_title) > 100:
        errors['job_title'] = "Job title must be 2–100 characters."
    else:
        cleaned['job_title'] = job_title

    # Year & months
    try:
        cleaned['year'] = validate_year(post_data.get('year'))
    except forms.ValidationError as e:
        errors['year'] = e.message

    try:
        cleaned['months'] = validate_months(post_data.getlist('months'))
    except forms.ValidationError as e:
        errors['months'] = e.message

    return cleaned, errors
