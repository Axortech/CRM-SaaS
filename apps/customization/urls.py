from rest_framework.routers import DefaultRouter

from apps.customization.views import CustomFieldViewSet, LayoutConfigurationViewSet

router = DefaultRouter()
router.register(r"settings/custom-fields", CustomFieldViewSet, basename="settings-custom-field")
router.register(r"settings/layouts", LayoutConfigurationViewSet, basename="settings-layout-configuration")

urlpatterns = router.urls
