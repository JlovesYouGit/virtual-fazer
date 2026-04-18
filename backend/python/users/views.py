from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.utils import timezone
from .models import User, UserProfile, UserActivity
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserProfileSerializer, UserActivitySerializer
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Log registration activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            metadata={'registration': True}
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Update last active
        user.last_active = timezone.now()
        user.save(update_fields=['last_active'])
        
        # Log login activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            metadata={'ip_address': request.META.get('REMOTE_ADDR')}
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data["refresh_token"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activity_view(request):
    activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:50]
    serializer = UserActivitySerializer(activities, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def track_activity(request):
    activity_type = request.data.get('activity_type')
    target_user_id = request.data.get('target_user_id')
    metadata = request.data.get('metadata', {})
    
    if not activity_type:
        return Response({'error': 'activity_type is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    target_user = None
    if target_user_id:
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({'error': 'Target user not found'}, status=status.HTTP_404_NOT_FOUND)
    
    activity = UserActivity.objects.create(
        user=request.user,
        activity_type=activity_type,
        target_user=target_user,
        metadata=metadata
    )
    
    return Response({'message': 'Activity tracked successfully'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def google_oauth_callback(request):
    """
    Handle Google OAuth callback - receives authorization code from Google
    """
    try:
        # Check for error parameters in callback
        error = request.GET.get('error')
        error_description = request.GET.get('error_description')
        
        if error:
            return Response({
                "error": error,
                "error_description": error_description,
                "message": f"Google OAuth failed: {error}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get authorization code from Google
        code = request.GET.get('code')
        state = request.GET.get('state')
        
        if not code:
            return Response({"error": "Authorization code not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Exchange code for access token
        import requests
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': '473715635548-phpqpcvcji0uilu7sg1tcdppv5aoc63u.apps.googleusercontent.com',
            'client_secret': '473715635548-phpqpcvcji0uilu7sg1tcdppv5aoc63u',
            'redirect_uri': 'http://localhost:5174/auth/callback/google/',
            'grant_type': 'authorization_code',
        }
        
        # POST to Google's token endpoint
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        if response.status_code != 200:
            return Response({"error": "Token exchange failed"}, status=status.HTTP_400_BAD_REQUEST)
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        id_token = token_data.get('id_token')
        
        # Verify ID token to get user info
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token
        
        request_session = Request()
        idinfo = id_token.verify_oauth2_token(
            id_token,
            request_session,
            '473715635548-phpqpcvcji0uilu7sg1tcdppv5aoc63u.apps.googleusercontent.com'
        )
        
        # Create or get user
        user, created = User.objects.get_or_create(
            email=idinfo['email'],
            defaults={
                'username': idinfo['email'].split('@')[0],
                'first_name': idinfo.get('given_name', ''),
                'last_name': idinfo.get('family_name', ''),
                'is_verified': True
            }
        )
        
        # Create social account link
        from socialaccount.models import SocialAccount
        SocialAccount.objects.get_or_create(
            user=user,
            provider='google',
            uid=idinfo['sub'],
            defaults={
                'extra_data': idinfo
            }
        )
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        # Redirect to frontend with tokens and success flag
        redirect_url = f"http://localhost:5174/auth/callback?access_token={refresh.access_token}&refresh_token={refresh.token}&user_id={user.id}&success=true"
        return redirect(redirect_url)
        
    except Exception as e:
        return Response({
            "error": str(e),
            "message": f"OAuth token exchange failed: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
