from rest_framework.routers import DefaultRouter

from apps.dashboard.views import DashboardMetricsViewSet, DashboardWidgetViewSet

router = DefaultRouter()
router.register(r"dashboard/metrics", DashboardMetricsViewSet, basename="dashboard-metrics")
router.register(r"dashboard/widgets", DashboardWidgetViewSet, basename="dashboard-widget")

urlpatterns = router.urls
