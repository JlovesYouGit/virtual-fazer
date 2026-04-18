from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, UserCategory, UserBehaviorPattern, UserActivity


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'bio', 
                 'profile_image', 'is_verified', 'date_of_birth', 'phone_number', 
                 'website', 'gender', 'created_at', 'last_active', 'profile')
        read_only_fields = ('id', 'is_verified', 'created_at', 'last_active')
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'followers_count': profile.followers_count,
                'following_count': profile.following_count,
                'posts_count': profile.posts_count,
                'is_private': profile.is_private,
                'show_activity_status': profile.show_activity_status,
                'language': profile.language,
                'timezone': profile.timezone,
            }
        except UserProfile.DoesNotExist:
            return None


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'


class UserCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCategory
        fields = '__all__'


class UserBehaviorPatternSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    category = UserCategorySerializer(read_only=True)
    
    class Meta:
        model = UserBehaviorPattern
        fields = '__all__'


class UserActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserActivity
        fields = '__all__'
