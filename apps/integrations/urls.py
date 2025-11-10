from rest_framework.routers import DefaultRouter

from apps.integrations.views import IntegrationKeyViewSet, WebhookViewSet

router = DefaultRouter()
router.register(r"settings/webhooks", WebhookViewSet, basename="settings-webhook")
router.register(r"integration-keys", IntegrationKeyViewSet, basename="integration-key")

urlpatterns = router.urls
