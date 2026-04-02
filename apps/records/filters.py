"""
Django-filter FilterSet for FinancialRecord.

Supports:
  ?type=income
  ?category=salary
  ?date_from=2024-01-01&date_to=2024-12-31
  ?search=rent          (notes + category full-text)
  ?ordering=-amount     (sort by any field)
"""

import django_filters
from .models import FinancialRecord


class FinancialRecordFilter(django_filters.FilterSet):
    # Exact match filters
    type     = django_filters.ChoiceFilter(choices=FinancialRecord.TransactionType.choices)
    category = django_filters.ChoiceFilter(choices=FinancialRecord.Category.choices)

    # Date range filters
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte', label='Date from (YYYY-MM-DD)')
    date_to   = django_filters.DateFilter(field_name='date', lookup_expr='lte', label='Date to (YYYY-MM-DD)')

    # Amount range filters
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte', label='Minimum amount')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte', label='Maximum amount')

    class Meta:
        model  = FinancialRecord
        fields = ['type', 'category', 'date_from', 'date_to', 'amount_min', 'amount_max']
