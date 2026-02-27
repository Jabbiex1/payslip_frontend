# payslip_app/validators.py
import re
from django import forms


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