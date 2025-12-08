from rest_framework.routers import DefaultRouter

from apps.dashboard.views import DashboardMetricsViewSet, DashboardWidgetViewSet

router = DefaultRouter()
router.register(r"organizations/(?P<organization_id>[^/.]+)/dashboard/stats", DashboardMetricsViewSet, basename="dashboard-stats")
router.register(r"dashboard/widgets", DashboardWidgetViewSet, basename="dashboard-widget")

urlpatterns = router.urls
