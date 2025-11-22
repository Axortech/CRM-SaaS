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
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    organization_name = serializers.CharField(max_length=255)
    timezone = serializers.CharField(max_length=64, default="UTC")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        org_name = validated_data.pop("organization_name")
        timezone = validated_data.pop("timezone", "UTC")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)

        organization = org_services.create_organization_with_owner(
            owner=user,
            name=org_name,
            timezone=timezone,
        )

        return {"user": user, "organization": organization}


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        memberships = OrganizationMember.objects.filter(
            user=self.user, is_active=True
        ).select_related("organization", "role")
        data["memberships"] = [
            {
                "organization_id": member.organization_id,
                "organization_name": member.organization.name,
                "role": member.role.name if member.role else None,
            }
            for member in memberships
        ]
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
