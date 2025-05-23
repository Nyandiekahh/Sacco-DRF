# sacco_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from authentication.views import VerifyDocumentView  # Add this import


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/members/', include('members.urls')),
    path('api/contributions/', include('contributions.urls')),
    path('api/loans/', include('loans.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/settings/', include('settings_api.urls')),
    path('api/admin/verify-document/<uuid:document_id>/', VerifyDocumentView.as_view(), name='verify-document-by-id'),
    path('api/admin/verify-document/type/<str:document_type>/', VerifyDocumentView.as_view(), name='verify-document-by-type'),
    
    # JWT token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)