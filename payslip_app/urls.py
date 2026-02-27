from django.urls import path
from . import views

from .views import generate_payslip_view
urlpatterns = [
    # FRONTEND (staff/admin login)
    path('', views.home_view, name='home'),
    path('frontend-admin/login/', views.admin_login_view, name='admin_login'),
    path('frontend-admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('frontend-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    path('frontend-admin/reports/export/', views.export_reports, name='export_reports'),
    path('frontend-admin/retrieval-logs/', views.retrieval_logs_view, name='admin_retrieval_logs'),

    # Actions
    path('frontend-admin/upload/<int:request_id>/', views.upload_payslip_view, name='upload_payslip'),
    path('frontend-admin/approve/<int:pk>/', views.approve_request, name='approve_request'),
    path('frontend-admin/reject/<int:pk>/', views.reject_request, name='reject_request'),
    path('frontend-admin/delete/<int:pk>/', views.delete_request, name='delete_request'),
    path("download/<int:file_id>/", views.download_payslip_view, name="download_payslip"),
    path('admin/mark-completed/<int:pk>/', views.mark_completed, name='mark_completed'),

    # EMPLOYEE VIEWS
    path('request/', views.request_form_view, name='request_form'),
    path('admin/notifications/', views.admin_notifications_view, name ='admin_notifications'),
    path('check/', views.check_payslip_view, name='check_payslip'),

 
    path('frontend-admin/notifications/', views.admin_notifications_view, name='admin_notifications'),
    path('generate/', generate_payslip_view, name='generate_form'),
    path('retrieval-logs/', views.retrieval_logs_view, name='retrieval_logs'),
    path('retrieval-logs/delete/<int:pk>/', views.delete_retrieval_log, name='delete_retrieval_log'),
        # Bulk action (POST only)
   path("frontend-admin/bulk-action/", views.bulk_action, name="bulk_action"),
    # Export retrieval logs to CSV
   path('frontend-admin/retrieval-logs/export/', views.export_retrieval_logs, name='export_retrieval_logs'),


    # Audit logs page
    path('frontend-admin/audit-logs/', views.admin_audit_logs_view, name='admin_audit_logs'),
    
]



handler429 = 'payslip_app.views.ratelimit_error'
