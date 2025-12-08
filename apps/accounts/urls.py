from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    AcceptInvitationView,
    CurrentUserView,
    CustomTokenObtainPairView,
    ForgotPasswordView,
    LogoutView,
    MFASetupView,
    MFAVerifyView,
    OAuthGoogleView,
    OAuthMicrosoftView,
    RegisterView,
    ResetPasswordView,
    UserActivityLogView,
    UserNotificationMarkAllReadView,
    UserNotificationReadView,
    UserNotificationsView,
    UserPasswordUpdateView,
    VerifyEmailView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("mfa/setup/", MFASetupView.as_view(), name="auth-mfa-setup"),
    path("mfa/verify/", MFAVerifyView.as_view(), name="auth-mfa-verify"),
    path("oauth/google/", OAuthGoogleView.as_view(), name="auth-oauth-google"),
    path("oauth/microsoft/", OAuthMicrosoftView.as_view(), name="auth-oauth-microsoft"),
    path("me/", CurrentUserView.as_view(), name="auth-me"),
    path("users/me/", CurrentUserView.as_view(), name="users-me"),
    path("users/me/password/", UserPasswordUpdateView.as_view(), name="users-me-password"),
    path("users/me/notifications/", UserNotificationsView.as_view(), name="users-me-notifications"),
    path("users/me/notifications/<uuid:notification_id>/read/", UserNotificationReadView.as_view(), name="users-me-notification-read"),
    path("users/me/notifications/mark-all-read/", UserNotificationMarkAllReadView.as_view(), name="users-me-notifications-mark-all-read"),
    path("users/me/activity-log/", UserActivityLogView.as_view(), name="users-me-activity-log"),
]
