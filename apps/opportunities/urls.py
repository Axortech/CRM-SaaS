from rest_framework.routers import DefaultRouter

from apps.opportunities.views import OpportunityStageViewSet, OpportunityViewSet

router = DefaultRouter()
router.register(r"opportunities", OpportunityViewSet, basename="opportunity")
router.register(r"settings/opportunity-stages", OpportunityStageViewSet, basename="settings-opportunity-stage")

urlpatterns = router.urls
