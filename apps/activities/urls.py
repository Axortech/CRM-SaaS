from rest_framework.routers import DefaultRouter

from apps.activities.views import ActivityViewSet

router = DefaultRouter()
router.register(r"activities", ActivityViewSet, basename="activity")

urlpatterns = router.urls
