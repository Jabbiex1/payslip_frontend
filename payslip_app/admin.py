from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

class UserAdmin(BaseUserAdmin):
    # Show a column with user's TOTP devices count
    def totp_device_count(self, obj):
        count = TOTPDevice.objects.filter(user=obj).count()
        return count
    totp_device_count.short_description = "2FA Devices"

    # Link to add/setup a TOTP device for this user
    def setup_2fa_link(self, obj):
        url = reverse('admin:otp_totp_totpdevice_add') + f'?user={obj.id}'
        return format_html('<a class="button" href="{}" target="_blank">Setup 2FA</a>', url)
    setup_2fa_link.short_description = "Setup 2FA"

    list_display = ('username', 'email', 'is_staff', 'is_active', 'totp_device_count', 'setup_2fa_link')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email')

# Unregister default User admin
admin.site.unregister(User)
# Register our customized User admin
admin.site.register(User, UserAdmin)
from django.contrib import admin
from .models import PayrollData

@admin.register(PayrollData)
class PayrollDataAdmin(admin.ModelAdmin):
    list_display = ('staff_number', 'full_name', 'month', 'year', 'notified')

    