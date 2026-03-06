class PayslipRouter:

    route_app_labels = {"payslip_app"}

    def db_for_read(self, model, **hints):
        if model.__name__ == "EmployeePayslip":
            return "mock_payslips"
        return "default"

    def db_for_write(self, model, **hints):
        if model.__name__ == "EmployeePayslip":
            return "mock_payslips"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name == "employeepayslip":
            return db == "mock_payslips"
        return db == "default"