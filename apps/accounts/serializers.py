from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.organizations import services as org_services
from apps.organizations.models import Organization, OrganizationMember, Role
from apps.accounts.models import EmailVerificationToken, PasswordResetToken


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar_url",
            "email_verified",
            "mfa_enabled",
        ]
        read_only_fields = ["id", "email", "email_verified", "mfa_enabled"]


class OrganizationSummarySerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = OrganizationMember
        fields = ["organization", "role"]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    
    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)

        # Create default organization with user's name or email
        org_name = f"{user.first_name}'s Organization" if user.first_name else f"{user.email}'s Organization"
        organization = org_services.create_organization_with_owner(
            owner=user,
            name=org_name,
            timezone="UTC",
        )

        return {"user": user, "organization": organization}


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["user"] = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "created_at": user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
        }
        return data


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()

    def validate(self, attrs):
        email = attrs["email"]
        token_value = attrs["token"]
        try:
            token = EmailVerificationToken.objects.select_related("user").get(
                token=token_value,
                user__email=email,
                is_used=False,
            )
        except EmailVerificationToken.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid verification token.") from exc

        if token.expires_at < timezone.now():
            raise serializers.ValidationError("Verification token has expired.")

        attrs["token_obj"] = token
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            attrs_user = User.objects.get(email=value)
        except User.DoesNotExist:
            attrs_user = None
        self.context["user"] = attrs_user
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        token_value = attrs["token"]
        try:
            token = PasswordResetToken.objects.select_related("user").get(
                token=token_value,
                is_used=False,
            )
        except PasswordResetToken.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid reset token.") from exc

        if token.expires_at < timezone.now():
            raise serializers.ValidationError("Reset token has expired.")

        attrs["token_obj"] = token
        return attrs


class MFAVerifySerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)


class OAuthLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
