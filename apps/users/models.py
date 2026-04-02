"""
Custom User Model

Extends Django's AbstractBaseUser to support role-based access control.
Using email as the primary login identifier (instead of username).

Roles:
  ADMIN   → full system access
  ANALYST → read + analytics
  VIEWER  → read-only
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager: create_user and create_superuser helpers."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault('role', User.Role.VIEWER)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.
    Primary key: auto BigInt (Django default).
    Login field: email.
    """

    class Role(models.TextChoices):
        ADMIN   = 'admin',   'Admin'
        ANALYST = 'analyst', 'Analyst'
        VIEWER  = 'viewer',  'Viewer'

    # ── Core fields ───────────────────────────────────────────────────────────
    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    role       = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)

    # ── Status ────────────────────────────────────────────────────────────────
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)   # Django admin access

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.full_name} ({self.email}) — {self.role}"

    # ── Computed properties ───────────────────────────────────────────────────
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_analyst(self):
        return self.role == self.Role.ANALYST

    @property
    def is_viewer(self):
        return self.role == self.Role.VIEWER
