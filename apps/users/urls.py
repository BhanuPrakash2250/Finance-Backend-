"""URL routes for the users app."""

from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    MeView,
    ChangePasswordView,
    UserListCreateView,
    UserDetailView,
)

urlpatterns = [
    # Auth
    path('login/',        LoginView.as_view(),          name='auth-login'),
    path('logout/',       LogoutView.as_view(),         name='auth-logout'),

    # Own profile
    path('me/',           MeView.as_view(),             name='auth-me'),
    path('me/password/',  ChangePasswordView.as_view(), name='auth-change-password'),

    # Admin: user management
    path('users/',        UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(),  name='user-detail'),
]
