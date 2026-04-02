from django.contrib import admin
from .models import FinancialRecord


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display  = ['id', 'type', 'category', 'amount', 'date', 'created_by', 'is_deleted']
    list_filter   = ['type', 'category', 'is_deleted', 'date']
    search_fields = ['notes', 'category']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
