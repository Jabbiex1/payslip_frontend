from rest_framework import serializers
from .models import PayslipRequest

class PayslipRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayslipRequest
        fields = '__all__'
