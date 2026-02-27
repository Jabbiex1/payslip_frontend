# middleware.py
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

class AutoLogoutOnLeaveMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and request.path.startswith('/frontend-admin/'):
            # Check a flag to see if they left page before
            if request.session.get('leave_flag', False):
                from django.contrib.auth import logout
                logout(request)
                return redirect('admin_login')
        return None

    def process_response(self, request, response):
        # Set leave_flag when dashboard is served
        if request.user.is_authenticated and request.path.startswith('/frontend-admin/'):
            request.session['leave_flag'] = True
        return response
