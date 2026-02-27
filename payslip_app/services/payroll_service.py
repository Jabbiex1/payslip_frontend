from ..models import PayrollData, EmployeePayslip

def fetch_employee_payslip(pin_code):
    """
    Currently uses mock database.
    Replace with external API call later.
    """
    try:
        return EmployeePayslip.objects.using('mock_payslips').get(pin_code=pin_code)
    except EmployeePayslip.DoesNotExist:
        return None

def fetch_payslips_for_notification(limit=1000):
    """
    Fetch pending payrolls for notifications.
    Can later pull from external payroll API.
    """
    return PayrollData.objects.filter(notified=False)[:limit]