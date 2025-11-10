import pyotp

from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import EmailVerificationToken, PasswordResetToken, User
from apps.accounts.serializers import (
    CustomTokenObtainPairSerializer,
    EmailVerificationSerializer,
    ForgotPasswordSerializer,
    MFAVerifySerializer,
    OAuthLoginSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)
from apps.notifications.models import AuditLogEntry, Notification
from apps.notifications.serializers import AuditLogSerializer, NotificationSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        output = serializer.save()
        user = output["user"]
        organization = output["organization"]
        verification_token = EmailVerificationToken.objects.create(user=user)
        refresh = RefreshToken.for_user(user)
        payload = {
            "user": UserSerializer(user).data,
            "organization": {
                "id": str(organization.id),
                "name": organization.name,
                "slug": organization.slug,
            },
            "email_verification_token": verification_token.token,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        return Response(payload, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class CurrentUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token_obj"]
        user = token.user
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        token.mark_used()
        return Response({"detail": "Email verified successfully."}, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.context.get("user")
        token_value = None
        if user:
            token = PasswordResetToken.objects.create(user=user)
            token_value = token.token
        return Response(
            {
                "detail": "If the account exists, a reset link has been sent.",
                "reset_token": token_value,
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token_obj"]
        user = token.user
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        token.mark_used()
        return Response({"detail": "Password reset successful."}, status=status.HTTP_200_OK)


class MFASetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = False
        user.save(update_fields=["mfa_secret", "mfa_enabled"])
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="CRM SaaS")
        return Response(
            {
                "secret": secret,
                "provisioning_uri": provisioning_uri,
            },
            status=status.HTTP_200_OK,
        )


class MFAVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not request.user.mfa_secret:
            return Response(
                {"detail": "MFA setup required before verification."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = MFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        totp = pyotp.TOTP(request.user.mfa_secret)
        if not totp.verify(serializer.validated_data["code"]):
            return Response({"detail": "Invalid MFA code."}, status=status.HTTP_400_BAD_REQUEST)
        request.user.mfa_enabled = True
        request.user.save(update_fields=["mfa_enabled"])
        return Response({"detail": "MFA verified successfully."}, status=status.HTTP_200_OK)


class OAuthBaseView(APIView):
    permission_classes = [permissions.AllowAny]
    provider = "oauth"

    def post(self, request, *args, **kwargs):
        serializer = OAuthLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        defaults = {
            "first_name": serializer.validated_data.get("first_name", ""),
            "last_name": serializer.validated_data.get("last_name", ""),
            "is_active": True,
        }
        user, created = User.objects.get_or_create(email=email, defaults=defaults)
        if created:
            user.email_verified = True
            user.set_unusable_password()
            user.save(update_fields=["email_verified", "password"])
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "provider": self.provider,
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class OAuthGoogleView(OAuthBaseView):
    provider = "google"


class OAuthMicrosoftView(OAuthBaseView):
    provider = "microsoft"


class UserPasswordUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        if not current_password or not new_password:
            return Response(
                {"detail": "Both current and new password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        if not user.check_password(current_password):
            return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated successfully."})


class UserNotificationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class UserNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, notification_id, *args, **kwargs):
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.read_at = request.data.get("read_at") or timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
        return Response(NotificationSerializer(notification).data)


class UserNotificationMarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return Response({"updated": updated})


class UserActivityLogView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        logs = AuditLogEntry.objects.filter(user=request.user).order_by("-timestamp")
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)
