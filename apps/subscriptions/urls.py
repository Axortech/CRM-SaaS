from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.subscriptions.views import PlanListView, SubscriptionViewSet

router = DefaultRouter()
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")

urlpatterns = [
    path("subscriptions/plans/", PlanListView.as_view(), name="subscription-plans"),
]

urlpatterns += router.urls
