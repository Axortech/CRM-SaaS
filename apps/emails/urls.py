from rest_framework.routers import DefaultRouter

from apps.emails.views import EmailCampaignViewSet, EmailTemplateViewSet, EmailViewSet

router = DefaultRouter()
router.register(r"email-templates", EmailTemplateViewSet, basename="email-template")
router.register(r"emails", EmailViewSet, basename="email")
router.register(r"email-campaigns", EmailCampaignViewSet, basename="email-campaign")

urlpatterns = router.urls
