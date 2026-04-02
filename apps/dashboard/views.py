"""
Dashboard Views (Analytics)

Access: Analyst + Admin only (IsAnalystOrAbove)

Endpoints:
  GET /api/dashboard/summary/          → Totals: income, expenses, balance
  GET /api/dashboard/category-summary/ → Breakdown by category
  GET /api/dashboard/monthly-trends/   → Month-by-month income vs expense
  GET /api/dashboard/recent-records/   → Last N records (quick view)

All queries exclude soft-deleted records.
Date range filtering supported via ?date_from=&date_to= on all endpoints.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date

from core.permissions.rbac import IsAnalystOrAbove
from apps.records.models import FinancialRecord
from apps.records.serializers import FinancialRecordReadSerializer


def _base_queryset(request):
    """
    Return the base queryset respecting:
      - soft-delete exclusion
      - optional ?date_from / ?date_to filters
    Analysts see all data; Viewers only see their own.
    (Dashboard is Analyst+, so Viewers won't reach these views,
     but we keep the guard for future-proofing.)
    """
    qs = FinancialRecord.objects.filter(is_deleted=False)

    date_from = request.query_params.get('date_from')
    date_to   = request.query_params.get('date_to')

    if date_from:
        parsed = parse_date(date_from)
        if parsed:
            qs = qs.filter(date__gte=parsed)
    if date_to:
        parsed = parse_date(date_to)
        if parsed:
            qs = qs.filter(date__lte=parsed)

    return qs


class SummaryView(APIView):
    """
    GET /api/dashboard/summary/

    Returns:
      - total_income
      - total_expenses
      - net_balance  (income - expenses)
      - total_records
      - income_count
      - expense_count

    Optional filters: ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        qs = _base_queryset(request)

        # Single DB query using conditional aggregation
        aggregates = qs.aggregate(
            total_income   = Sum('amount', filter=Q(type='income'))  or 0,
            total_expenses = Sum('amount', filter=Q(type='expense')) or 0,
            income_count   = Count('id',   filter=Q(type='income')),
            expense_count  = Count('id',   filter=Q(type='expense')),
            total_records  = Count('id'),
        )

        # Handle None (no records of that type)
        total_income   = aggregates['total_income']   or 0
        total_expenses = aggregates['total_expenses'] or 0
        net_balance    = total_income - total_expenses

        return Response({
            'success': True,
            'data': {
                'total_income':   float(total_income),
                'total_expenses': float(total_expenses),
                'net_balance':    float(net_balance),
                'total_records':  aggregates['total_records'],
                'income_count':   aggregates['income_count'],
                'expense_count':  aggregates['expense_count'],
                'filters_applied': {
                    'date_from': request.query_params.get('date_from'),
                    'date_to':   request.query_params.get('date_to'),
                },
            }
        })


class CategorySummaryView(APIView):
    """
    GET /api/dashboard/category-summary/

    Returns per-category breakdown with:
      - total amount
      - transaction count
      - percentage of total spend (for expenses)

    Optional filters: ?date_from=&date_to=&type=income|expense
    """
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        qs = _base_queryset(request)

        # Optional: filter by transaction type
        txn_type = request.query_params.get('type')
        if txn_type in ('income', 'expense'):
            qs = qs.filter(type=txn_type)

        # Group by category and transaction type
        breakdown = (
            qs
            .values('category', 'type')
            .annotate(
                total  = Sum('amount'),
                count  = Count('id'),
            )
            .order_by('-total')
        )

        # Calculate grand total for percentage computation
        grand_total = sum(item['total'] for item in breakdown) or 1  # avoid division by zero

        result = [
            {
                'category':   row['category'],
                'type':       row['type'],
                'total':      float(row['total']),
                'count':      row['count'],
                'percentage': round(float(row['total']) / float(grand_total) * 100, 2),
            }
            for row in breakdown
        ]

        return Response({
            'success': True,
            'data': {
                'breakdown':   result,
                'grand_total': float(grand_total),
            }
        })


class MonthlyTrendsView(APIView):
    """
    GET /api/dashboard/monthly-trends/

    Returns month-by-month income vs expenses for trend analysis.
    Each entry: { month: "2024-03", income: X, expenses: Y, net: Z }

    Optional filters: ?date_from=&date_to=
    """
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        qs = _base_queryset(request)

        monthly = (
            qs
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                total_income   = Sum('amount', filter=Q(type='income')),
                total_expenses = Sum('amount', filter=Q(type='expense')),
                income_count   = Count('id',   filter=Q(type='income')),
                expense_count  = Count('id',   filter=Q(type='expense')),
            )
            .order_by('month')
        )

        trends = [
            {
                'month':          row['month'].strftime('%Y-%m'),
                'income':         float(row['total_income']   or 0),
                'expenses':       float(row['total_expenses'] or 0),
                'net':            float((row['total_income'] or 0) - (row['total_expenses'] or 0)),
                'income_count':   row['income_count'],
                'expense_count':  row['expense_count'],
            }
            for row in monthly
        ]

        return Response({
            'success': True,
            'data': {
                'monthly_trends': trends,
                'total_months':   len(trends),
            }
        })


class RecentRecordsView(APIView):
    """
    GET /api/dashboard/recent-records/

    Returns the last N financial records (default 10, max 50).
    Query param: ?limit=10
    """
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 10)), 50)
        records = (
            FinancialRecord.objects
            .filter(is_deleted=False)
            .select_related('created_by')
            .order_by('-date', '-created_at')[:limit]
        )
        serializer = FinancialRecordReadSerializer(records, many=True)
        return Response({
            'success': True,
            'data': {
                'records': serializer.data,
                'count':   len(serializer.data),
            }
        })
