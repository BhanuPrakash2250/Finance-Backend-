"""
Financial Records Views

RBAC rules applied here:
  - GET (list/detail)  → Viewer, Analyst, Admin
  - POST (create)      → Admin only
  - PUT/PATCH (update) → Admin only
  - DELETE (soft)      → Admin only

Filtering, search, ordering, and pagination are all supported.
"""

from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions.rbac import IsAdmin, IsViewerOrAbove
from .models import FinancialRecord
from .serializers import FinancialRecordSerializer, FinancialRecordReadSerializer
from .filters import FinancialRecordFilter


class FinancialRecordListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/records/       → List records (all authenticated users)
    POST /api/records/       → Create record (Admin only)

    Supports:
      Filtering  → ?type=income&category=salary&date_from=2024-01-01
      Searching  → ?search=freelance   (searches notes and category)
      Ordering   → ?ordering=-amount,-date
      Pagination → ?page=2&page_size=10
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class  = FinancialRecordFilter
    search_fields    = ['notes', 'category']       # ?search=
    ordering_fields  = ['amount', 'date', 'created_at', 'category', 'type']
    ordering         = ['-date']                   # default ordering

    def get_queryset(self):
        """
        Admins and Analysts see all records.
        Viewers see only their own records.
        Soft-deleted records are always excluded.
        """
        qs = FinancialRecord.objects.filter(is_deleted=False).select_related('created_by')

        user = self.request.user
        if user.role == 'viewer':
            qs = qs.filter(created_by=user)

        return qs

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsViewerOrAbove()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FinancialRecordSerializer
        # Viewers get a trimmed-down read serializer
        if self.request.user.role == 'viewer':
            return FinancialRecordReadSerializer
        return FinancialRecordSerializer

    def create(self, request, *args, **kwargs):
        serializer = FinancialRecordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response(
            {'success': True, 'message': 'Record created.', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )


class FinancialRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/records/<id>/  → Retrieve (Viewer, Analyst, Admin)
    PUT    /api/records/<id>/  → Full update (Admin only)
    PATCH  /api/records/<id>/  → Partial update (Admin only)
    DELETE /api/records/<id>/  → Soft delete (Admin only)
    """

    def get_queryset(self):
        return FinancialRecord.objects.filter(is_deleted=False).select_related('created_by')

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsViewerOrAbove()]

    def get_serializer_class(self):
        if self.request.user.role == 'viewer':
            return FinancialRecordReadSerializer
        return FinancialRecordSerializer

    def retrieve(self, request, *args, **kwargs):
        record = self.get_object()
        serializer = self.get_serializer(record)
        return Response({'success': True, 'data': serializer.data})

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        record     = self.get_object()
        serializer = FinancialRecordSerializer(
            record, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'message': 'Record updated.', 'data': serializer.data})

    def destroy(self, request, *args, **kwargs):
        """Soft delete — mark as deleted, never physically remove."""
        record = self.get_object()
        record.is_deleted = True
        record.save()
        return Response(
            {'success': True, 'message': f'Record #{record.id} has been deleted.'},
            status=status.HTTP_200_OK
        )
