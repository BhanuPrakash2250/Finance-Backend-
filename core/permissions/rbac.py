"""
Role-Based Access Control (RBAC) Permission Classes

The system has three roles (defined on the User model):
  - ADMIN    → full access: read, write, delete, dashboard, user management
  - ANALYST  → read access + full dashboard/analytics
  - VIEWER   → read-only access to financial records

Usage in views:
    permission_classes = [IsAuthenticated, IsAdmin]
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    permission_classes = [IsAuthenticated, IsViewerOrAbove]
"""

from rest_framework.permissions import BasePermission
from apps.users.models import User


class IsAdmin(BasePermission):
    """Only Admin users can access this endpoint."""
    message = "Access restricted to Administrators only."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == User.Role.ADMIN
        )


class IsAnalystOrAbove(BasePermission):
    """Analysts and Admins can access this endpoint."""
    message = "Access restricted to Analysts and Administrators."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [User.Role.ADMIN, User.Role.ANALYST]
        )


class IsViewerOrAbove(BasePermission):
    """All authenticated users (Viewer, Analyst, Admin) can access."""
    message = "Authentication required."

    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsAdminOrReadOnly(BasePermission):
    """
    Admins can do anything.
    Analysts and Viewers get read-only (safe methods: GET, HEAD, OPTIONS).
    """
    message = "Only Administrators can modify records."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.role == User.Role.ADMIN


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level: the owner of a record or an Admin can access it.
    Attach to views that expose individual objects.
    """
    message = "You can only access your own records."

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True
        return getattr(obj, 'created_by', None) == request.user
