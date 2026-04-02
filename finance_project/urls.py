"""
Root URL configuration for Finance Data Processing System.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# ─── Swagger Schema Setup ─────────────────────────────────────────────────────
schema_view = get_schema_view(
    openapi.Info(
        title="Finance Data Processing API",
        default_version='v1',
        description=(
            "A complete Finance Data Processing and Access Control System.\n\n"
            "**Roles:**\n"
            "- `Admin` — Full access (CRUD + dashboard + user management)\n"
            "- `Analyst` — Read + analytics (dashboard access)\n"
            "- `Viewer` — Read-only access to records\n\n"
            "**Authentication:** Use `/api/auth/login/` to get a Bearer token, "
            "then set `Authorization: Bearer <token>` on subsequent requests."
        ),
        contact=openapi.Contact(email="admin@financesystem.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # ── Authentication ────────────────────────────────────────────────────────
    path('api/auth/', include('apps.users.urls')),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── Core Resources ────────────────────────────────────────────────────────
    path('api/records/', include('apps.records.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),

    # ── Swagger Docs ──────────────────────────────────────────────────────────
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
