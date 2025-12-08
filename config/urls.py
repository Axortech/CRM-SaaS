"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

import apps.accounts.views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/invitations/<str:token>/accept/", apps.accounts.views.AcceptInvitationView.as_view(), name="invitation-accept"),
    path("api/v1/", include("apps.organizations.urls")),
    path("api/v1/", include("apps.subscriptions.urls")),
    path("api/v1/", include("apps.contacts.urls")),
    path("api/v1/", include("apps.leads.urls")),
    path("api/v1/", include("apps.companies.urls")),
    path("api/v1/", include("apps.opportunities.urls")),
    path("api/v1/", include("apps.tasks.urls")),
    path("api/v1/", include("apps.activities.urls")),
    path("api/v1/", include("apps.emails.urls")),
    path("api/v1/", include("apps.reports.urls")),
    path("api/v1/", include("apps.customization.urls")),
    path("api/v1/", include("apps.integrations.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.dashboard.urls")),
]
