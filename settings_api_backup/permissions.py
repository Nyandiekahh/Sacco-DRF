from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit settings.
    """
    def has_permission(self, request, view):
        # Check if user is admin (works with both is_staff and custom role field)
        return (
            request.user and 
            (request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN')
        )