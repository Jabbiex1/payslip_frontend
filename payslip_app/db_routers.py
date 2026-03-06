class PayslipRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'payslip_app':
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'payslip_app':
            return 'default'
        return None