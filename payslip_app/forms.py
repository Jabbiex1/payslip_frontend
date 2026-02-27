from django import forms

class PayslipRequestForm(forms.Form):
    pin_code = forms.CharField(max_length=10, label="Employee PIN")
    month = forms.IntegerField(min_value=1, max_value=12, label="Month")
    year = forms.IntegerField(min_value=2000, max_value=2100, label="Year")
    from django import forms

class ReferenceCodeForm(forms.Form):
    pin_code = forms.CharField(max_length=10, label="Employee Pin Code")
    month = forms.ChoiceField(
        choices=[
            ('01', 'January'),
            ('02', 'February'),
            ('03', 'March'),
            # ... add all months
        ],
        label="Month"
    )