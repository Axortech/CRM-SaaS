from rest_framework.routers import DefaultRouter

from apps.contacts.views import ContactViewSet

router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contact")

urlpatterns = router.urls
