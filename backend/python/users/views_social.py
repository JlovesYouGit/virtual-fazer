from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
import requests
import json

from .models import UserProfile
from .serializers_social import (
    GoogleLoginSerializer, SocialLoginResponseSerializer, 
    EmailVerificationSerializer, PasswordResetSerializer, SetPasswordSerializer,
    LinkSocialAccountSerializer, UnlinkSocialAccountSerializer,
    UserProfileSocialSerializer, SocialUserRegistrationSerializer
)

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Handle Google OAuth login
    """
    serializer = GoogleLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    access_token = serializer.validated_data['access_token']
    id_token = serializer.validated_data.get('id_token')
    
    try:
        # Verify the Google ID token
        if id_token:
            idinfo = id_token.verify_oauth2_token(
                id_token,
                requests.Request(),
                audience=request.META.get('HTTP_HOST')
            )
            
            email = idinfo.get('email')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            google_id = idinfo.get('sub')
            picture = idinfo.get('picture', '')
        else:
            # Get user info from Google API using access token
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            user_info = response.json()
            
            email = user_info.get('email')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            google_id = user_info.get('id')
            picture = user_info.get('picture', '')
        
        # Check if user exists with this Google account
        try:
            social_account = SocialAccount.objects.get(
                provider='google',
                uid=google_id
            )
            user = social_account.user
            
            # Update user profile with Google data
            if picture and hasattr(user, 'userprofile'):
                user.userprofile.profile_image = picture
                user.userprofile.save()
            
            # Login user and generate tokens
            login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_image': user.userprofile.profile_image if hasattr(user, 'userprofile') else None
                },
                'social_account': {
                    'provider': 'google',
                    'uid': google_id,
                    'extra_data': social_account.extra_data
                },
                'message': 'Login successful'
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except SocialAccount.DoesNotExist:
            # User doesn't exist, return error with registration info
            return Response({
                'error': 'account_not_found',
                'message': 'No account found with this Google account',
                'registration_data': {
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'google_id': google_id,
                    'picture': picture
                }
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'error': 'google_auth_failed',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_register(request):
    """
    Register a new user using Google OAuth
    """
    serializer = SocialUserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    access_token = serializer.validated_data['access_token']
    id_token = serializer.validated_data.get('id_token')
    username = serializer.validated_data.get('username')
    email = serializer.validated_data.get('email')
    first_name = serializer.validated_data.get('first_name')
    last_name = serializer.validated_data.get('last_name')
    
    try:
        # Verify the Google ID token
        if id_token:
            idinfo = id_token.verify_oauth2_token(
                id_token,
                requests.Request(),
                audience=request.META.get('HTTP_HOST')
            )
            
            google_email = idinfo.get('email')
            google_first_name = idinfo.get('given_name', '')
            google_last_name = idinfo.get('family_name', '')
            google_id = idinfo.get('sub')
            picture = idinfo.get('picture', '')
        else:
            # Get user info from Google API
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            user_info = response.json()
            
            google_email = user_info.get('email')
            google_first_name = user_info.get('given_name', '')
            google_last_name = user_info.get('family_name', '')
            google_id = user_info.get('id')
            picture = user_info.get('picture', '')
        
        # Use provided data or fall back to Google data
        final_email = email or google_email
        final_username = username or google_email.split('@')[0] if google_email else f'user_{google_id[:8]}'
        final_first_name = first_name or google_first_name
        final_last_name = last_name or google_last_name
        
        # Check if user already exists
        if User.objects.filter(email=final_email).exists():
            return Response({
                'error': 'email_exists',
                'message': 'User with this email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=final_username).exists():
            return Response({
                'error': 'username_exists',
                'message': 'Username already taken'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new user
        user = User.objects.create_user(
            username=final_username,
            email=final_email,
            first_name=final_first_name,
            last_name=final_last_name,
            is_active=True
        )
        
        # Create user profile
        UserProfile.objects.create(
            user=user,
            profile_image=picture,
            is_verified=True  # Google users are considered verified
        )
        
        # Create social account
        social_account = SocialAccount.objects.create(
            user=user,
            provider='google',
            uid=google_id,
            extra_data={
                'name': f'{final_first_name} {final_last_name}',
                'given_name': final_first_name,
                'family_name': final_last_name,
                'picture': picture,
                'email': final_email
            }
        )
        
        # Login user and generate tokens
        login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_image': user.userprofile.profile_image
            },
            'social_account': {
                'provider': 'google',
                'uid': google_id,
                'extra_data': social_account.extra_data
            },
            'message': 'Registration successful'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'registration_failed',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_google_account(request):
    """
    Link Google account to existing user
    """
    serializer = LinkSocialAccountSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    access_token = serializer.validated_data['access_token']
    id_token = serializer.validated_data.get('id_token')
    
    try:
        # Verify the Google ID token
        if id_token:
            idinfo = id_token.verify_oauth2_token(
                id_token,
                requests.Request(),
                audience=request.META.get('HTTP_HOST')
            )
            
            google_id = idinfo.get('sub')
            email = idinfo.get('email')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            picture = idinfo.get('picture', '')
        else:
            # Get user info from Google API
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            user_info = response.json()
            
            google_id = user_info.get('id')
            email = user_info.get('email')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            picture = user_info.get('picture', '')
        
        # Check if Google account is already linked to another user
        if SocialAccount.objects.filter(provider='google', uid=google_id).exists():
            return Response({
                'error': 'account_already_linked',
                'message': 'This Google account is already linked to another user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already has Google account linked
        if request.user.socialaccount_set.filter(provider='google').exists():
            return Response({
                'error': 'already_linked',
                'message': 'You already have a Google account linked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create social account link
        social_account = SocialAccount.objects.create(
            user=request.user,
            provider='google',
            uid=google_id,
            extra_data={
                'name': f'{first_name} {last_name}',
                'given_name': first_name,
                'family_name': last_name,
                'picture': picture,
                'email': email
            }
        )
        
        # Update user profile with Google picture
        if picture and hasattr(request.user, 'userprofile'):
            request.user.userprofile.profile_image = picture
            request.user.userprofile.save()
        
        return Response({
            'message': 'Google account linked successfully',
            'social_account': {
                'provider': 'google',
                'uid': google_id,
                'extra_data': social_account.extra_data
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'linking_failed',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_google_account(request):
    """
    Unlink Google account from user
    """
    serializer = UnlinkSocialAccountSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    provider = serializer.validated_data['provider']
    
    try:
        social_account = get_object_or_404(
            SocialAccount,
            user=request.user,
            provider=provider
        )
        
        social_account.delete()
        
        return Response({
            'message': f'{provider.capitalize()} account unlinked successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'unlinking_failed',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_social_accounts(request):
    """
    Get user's linked social accounts
    """
    social_accounts = request.user.socialaccount_set.all()
    
    serializer = SocialAccountSerializer(social_accounts, many=True)
    
    return Response({
        'social_accounts': serializer.data,
        'linked_providers': list(social_accounts.values_list('provider', flat=True))
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def google_exchange_code(request):
    """
    Exchange Google OAuth authorization code for tokens
    """
    code = request.data.get('code')
    
    if not code:
        return Response({
            'error': 'missing_code',
            'message': 'Authorization code is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Exchange the authorization code for tokens
        # This requires Google OAuth client credentials
        token_response = requests.post('https://oauth2.googleapis.com/token', {
            'client_id': '473715635548-phpqpcvcji0uilu7sg1tcdppv5aoc63u.apps.googleusercontent.com',
            'client_secret': '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7Q2L3',  # This should be in environment variables
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://localhost:5175/auth/callback/google/'
        })
        
        if not token_response.ok:
            return Response({
                'error': 'token_exchange_failed',
                'message': 'Failed to exchange authorization code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # Get user info from Google API
        user_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if not user_response.ok:
            return Response({
                'error': 'user_info_failed',
                'message': 'Failed to retrieve user information'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_info = user_response.json()
        email = user_info.get('email')
        google_id = user_info.get('id')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        picture = user_info.get('picture', '')
        
        # Check if user exists with this Google account
        try:
            social_account = SocialAccount.objects.get(
                provider='google',
                uid=google_id
            )
            user = social_account.user
            
            # Update user profile with Google data
            if picture and hasattr(user, 'userprofile'):
                user.userprofile.profile_image = picture
                user.userprofile.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_image': user.userprofile.profile_image if hasattr(user, 'userprofile') else None,
                    'is_verified': user.userprofile.is_verified if hasattr(user, 'userprofile') else False,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except SocialAccount.DoesNotExist:
            # User doesn't exist, create a new account
            username = email.split('@')[0] if email else f'user_{google_id[:8]}'
            
            # Ensure username is unique
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
            
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                profile_image=picture,
                is_verified=True  # Google users are considered verified
            )
            
            # Create social account
            social_account = SocialAccount.objects.create(
                user=user,
                provider='google',
                uid=google_id,
                extra_data={
                    'name': f'{first_name} {last_name}',
                    'given_name': first_name,
                    'family_name': last_name,
                    'picture': picture,
                    'email': email
                }
            )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_image': user.userprofile.profile_image,
                    'is_verified': user.userprofile.is_verified,
                    'date_joined': user.date_joined.isoformat()
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({
            'error': 'exchange_failed',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_with_social(request):
    """
    Get user profile with social account information
    """
    serializer = UserProfileSocialSerializer(request.user)
    
    return Response(serializer.data)
