# reports/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet,
    FinancialStatementViewSet,
    MemberStatementViewSet,
    AuditLogViewSet,
    SystemBackupViewSet,
    SavedReportViewSet
)

# Create a router for viewsets
router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'financial-statements', FinancialStatementViewSet, basename='financial-statement')
router.register(r'member-statements', MemberStatementViewSet, basename='member-statement')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'backups', SystemBackupViewSet, basename='system-backup')
router.register(r'saved-reports', SavedReportViewSet, basename='saved-report')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
]