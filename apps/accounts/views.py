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
from apps.organizations.models import Invitation, OrganizationMember
from apps.organizations.serializers import InvitationAcceptSerializer


class RegisterView(APIView):
    """
    Register a new user and create their organization.
    
    Creates a new user account and automatically creates an organization
    with the user as the owner. Returns JWT tokens for immediate authentication.
    """
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
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "created_at": user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
            }
        }
        return Response(payload, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login endpoint to obtain JWT access and refresh tokens.
    
    Returns access token, refresh token, and user information.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current authenticated user's profile.
    
    GET: Returns the current user's profile information.
    PATCH: Updates the current user's profile information.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """
    Logout the current user.
    
    Invalidates the current session. In a production environment,
    you may want to blacklist the JWT token here.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


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


class AcceptInvitationView(APIView):
    """
    Accept an invitation to join an organization.
    
    This is a public endpoint that accepts an invitation token.
    Can either link to an existing user or create a new user account.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, token, *args, **kwargs):
        try:
            invitation = Invitation.objects.select_related("organization", "role").prefetch_related("teams").get(token=token)
        except Invitation.DoesNotExist:
            return Response(
                {"error": "Invalid invitation token."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if invitation is valid
        if invitation.status != Invitation.Status.PENDING:
            return Response(
                {"error": "Invitation is not pending."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired():
            invitation.status = Invitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            return Response(
                {"error": "Invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data.get("user_id")
        password = serializer.validated_data.get("password")
        first_name = serializer.validated_data.get("first_name")
        last_name = serializer.validated_data.get("last_name")
        
        # Get or create user
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                if user.email != invitation.email:
                    return Response(
                        {"error": "User email does not match invitation email."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Create new user
            user = User.objects.create_user(
                email=invitation.email,
                password=password,
                first_name=first_name,
                last_name=last_name or "",
            )
        
        # Create organization member
        member, created = OrganizationMember.objects.get_or_create(
            organization=invitation.organization,
            user=user,
            defaults={
                "role": invitation.role,
                "invitation_accepted": True,
            }
        )
        
        if not created:
            # Update existing member
            member.role = invitation.role
            member.invitation_accepted = True
            member.is_active = True
            member.save(update_fields=["role", "invitation_accepted", "is_active"])
        
        # Add to teams
        if invitation.teams.exists():
            member.teams.set(invitation.teams.all())
        
        # Mark invitation as accepted
        invitation.mark_accepted()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "created_at": user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
            }
        }, status=status.HTTP_200_OK)
