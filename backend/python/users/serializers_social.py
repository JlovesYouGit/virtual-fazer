from rest_framework import serializers
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.provider import GoogleProvider

User = get_user_model()


class SocialAccountSerializer(serializers.ModelSerializer):
    """Serializer for social account information"""
    class Meta:
        model = SocialAccount
        fields = ('id', 'provider', 'uid', 'extra_data', 'date_joined')
        read_only_fields = ('id', 'provider', 'uid', 'date_joined')


class GoogleLoginSerializer(serializers.Serializer):
    """Serializer for Google OAuth login request"""
    access_token = serializers.CharField(max_length=255)
    id_token = serializers.CharField(max_length=500, required=False)


class SocialLoginResponseSerializer(serializers.Serializer):
    """Response serializer for social login"""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = serializers.DictField()
    social_account = serializers.DictField()
    message = serializers.CharField(default="Social login successful")


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    email = serializers.EmailField()
    key = serializers.CharField(max_length=255)


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset"""
    email = serializers.EmailField()


class SetPasswordSerializer(serializers.Serializer):
    """Serializer for setting new password"""
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class LinkSocialAccountSerializer(serializers.Serializer):
    """Serializer for linking social account to existing user"""
    provider = serializers.ChoiceField(choices=['google'])
    access_token = serializers.CharField(max_length=255)
    id_token = serializers.CharField(max_length=500, required=False)


class UnlinkSocialAccountSerializer(serializers.Serializer):
    """Serializer for unlinking social account"""
    provider = serializers.ChoiceField(choices=['google'])


class UserProfileSocialSerializer(serializers.ModelSerializer):
    """Extended user profile serializer with social account info"""
    social_accounts = SocialAccountSerializer(source='socialaccount_set', many=True, read_only=True)
    is_google_linked = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'profile_image', 'is_verified', 'date_joined', 
                 'social_accounts', 'is_google_linked')
        read_only_fields = ('id', 'username', 'email', 'date_joined', 'social_accounts')
    
    def get_is_google_linked(self, obj):
        return obj.socialaccount_set.filter(provider='google').exists()


class SocialUserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration via social account"""
    access_token = serializers.CharField(max_length=255)
    id_token = serializers.CharField(max_length=500, required=False)
    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)
    
    def validate(self, attrs):
        # For social registration, we need at least access_token
        if not attrs.get('access_token'):
            raise serializers.ValidationError("Access token is required")
        return attrs
