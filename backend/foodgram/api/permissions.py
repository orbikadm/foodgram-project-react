from rest_framework.permissions import SAFE_METHODS, BasePermission

class AdminOrReadOnly(BasePermission):

    def has_object_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_active
            and request.user.is_staff
        )