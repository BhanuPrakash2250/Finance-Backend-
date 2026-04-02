"""URL routes for dashboard / analytics endpoints."""

from django.urls import path
from .views import (
    SummaryView,
    CategorySummaryView,
    MonthlyTrendsView,
    RecentRecordsView,
)

urlpatterns = [
    path('summary/',          SummaryView.as_view(),         name='dashboard-summary'),
    path('category-summary/', CategorySummaryView.as_view(), name='dashboard-category'),
    path('monthly-trends/',   MonthlyTrendsView.as_view(),   name='dashboard-monthly'),
    path('recent-records/',   RecentRecordsView.as_view(),   name='dashboard-recent'),
]
