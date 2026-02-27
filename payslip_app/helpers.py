from django.db import connection
from django.utils import timezone
from .models import AdminAuditLog

def audit(request, action: str, target: str = None, detail: str = None):
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR')
    )

    AdminAuditLog.objects.create(
        admin=request.user if request.user.is_authenticated else None,
        action=action,
        target=target,
        detail=detail,
        ip_address=ip or None,
    )