# sacco_project/urls.py - Updated without settings_api

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from authentication.views import VerifyDocumentView

def api_root(request):
    """API root endpoint with available endpoints"""
    return JsonResponse({
        'message': 'Welcome to KMS SACCO API',
        'version': '1.0',
        'endpoints': {
            'admin': '/admin/',
            'api_docs': '/api/',
            'authentication': {
                'invite': '/api/auth/invite/',
                'login': '/api/auth/otp-login/',
                'register': '/api/auth/complete-registration/',
                'profile': '/api/auth/profile/',
                'token': '/api/token/',
                'token_refresh': '/api/token/refresh/',
            },
            'members': {
                'dashboard': '/api/members/dashboard/',
                'profile': '/api/members/profile/',
                'members_list': '/api/members/members/',
            },
            'contributions': {
                'monthly': '/api/contributions/monthly/',
                'share_capital': '/api/contributions/share-capital/',
            },
            'loans': {
                'applications': '/api/loans/applications/',
                'loans': '/api/loans/loans/',
                'eligibility': '/api/loans/eligibility/',
            },
            'reports': '/api/reports/reports/',
            'transactions': '/api/transactions/expenses/',
        },
        'documentation': 'Visit /api/ for detailed API documentation'
    })

def health_check(request):
    """Health check endpoint"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'service': 'KMS SACCO API'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy', 
            'error': str(e)
        }, status=500)

urlpatterns = [
    # Root endpoint
    path('', api_root, name='api-root'),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include([
        # API documentation endpoint
        path('', api_root, name='api-documentation'),
        
        # Authentication
        path('auth/', include('authentication.urls')),
        
        # Members
        path('members/', include('members.urls')),
        
        # Contributions
        path('contributions/', include('contributions.urls')),
        
        # Loans
        path('loans/', include('loans.urls')),
        
        # Transactions
        path('transactions/', include('transactions.urls')),
        
        # Reports
        path('reports/', include('reports.urls')),
        
        # JWT token endpoints
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ])),
    
    # Document verification endpoints
    path('api/admin/verify-document/<uuid:document_id>/', 
         VerifyDocumentView.as_view(), name='verify-document-by-id'),
    path('api/admin/verify-document/type/<str:document_type>/', 
         VerifyDocumentView.as_view(), name='verify-document-by-type'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)