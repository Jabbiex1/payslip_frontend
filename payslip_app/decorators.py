# decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def frontend_admin_required(view_func):
    @login_required(login_url='/frontend-admin/login/')
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:   # <-- use is_staff instead of is_frontend_admin
            return redirect('/frontend-admin/login/')
        return view_func(request, *args, **kwargs)
    return wrapped