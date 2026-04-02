"""
FinancialRecord Model

Represents a single financial transaction (income or expense).
Each record is owned by the user who created it.

Key design decisions:
  - amount stored as DecimalField (avoid float rounding errors in money)
  - category is a free-text CharField for flexibility; could be FK to a
    Category model if strict control is needed
  - soft-delete via is_deleted flag (preserve audit history)
  - created_by FK allows per-user ownership checks
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class FinancialRecord(models.Model):

    class TransactionType(models.TextChoices):
        INCOME  = 'income',  'Income'
        EXPENSE = 'expense', 'Expense'

    class Category(models.TextChoices):
        SALARY      = 'salary',      'Salary'
        FREELANCE   = 'freelance',   'Freelance'
        INVESTMENT  = 'investment',  'Investment'
        RENT        = 'rent',        'Rent'
        UTILITIES   = 'utilities',   'Utilities'
        GROCERIES   = 'groceries',   'Groceries'
        TRANSPORT   = 'transport',   'Transport'
        HEALTHCARE  = 'healthcare',  'Healthcare'
        EDUCATION   = 'education',   'Education'
        DINING      = 'dining',      'Dining'
        SHOPPING    = 'shopping',    'Shopping'
        TRAVEL      = 'travel',      'Travel'
        OTHER       = 'other',       'Other'

    # ── Core fields ───────────────────────────────────────────────────────────
    amount   = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Transaction amount (must be > 0)."
    )
    type     = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        help_text="'income' or 'expense'."
    )
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER,
        help_text="Transaction category."
    )
    date     = models.DateField(
        help_text="Date the transaction occurred (YYYY-MM-DD)."
    )
    notes    = models.TextField(
        blank=True,
        default='',
        help_text="Optional notes or description."
    )

    # ── Ownership & audit ─────────────────────────────────────────────────────
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='financial_records',
        help_text="User who created this record."
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft-delete flag. Records are never physically removed."
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_records'
        ordering = ['-date', '-created_at']
        indexes  = [
            # Speed up the most common filter combinations
            models.Index(fields=['type', 'date']),
            models.Index(fields=['category', 'date']),
            models.Index(fields=['created_by', 'date']),
        ]
        verbose_name = 'Financial Record'
        verbose_name_plural = 'Financial Records'

    def __str__(self):
        return f"{self.type.upper()} | {self.category} | ${self.amount} | {self.date}"
