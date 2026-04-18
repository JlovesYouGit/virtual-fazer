from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404
from django.conf import settings
import uuid

from .models import UserProfile
from .serializers_social import EmailVerificationSerializer, PasswordResetSerializer, SetPasswordSerializer

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def send_email_verification(request):
    """
    Send email verification link
    """
    serializer = EmailVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
        
        # Generate verification token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create verification URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
        
        # Send email
        subject = 'Verify your Instagran account'
        message = render_to_string('emails/email_verification.html', {
            'user': user,
            'verification_url': verification_url,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=message,
            fail_silently=False
        )
        
        return Response({
            'message': 'Verification email sent successfully',
            'email': email
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # Don't reveal if email exists or not
        return Response({
            'message': 'If this email exists in our system, a verification link has been sent.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'email_send_failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request, uidb64, token):
    """
    Verify email using token
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            
            # Update user profile
            if hasattr(user, 'userprofile'):
                user.userprofile.is_verified = True
                user.userprofile.save()
            
            return Response({
                'message': 'Email verified successfully',
                'status': 'verified'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'invalid_token',
                'message': 'Verification link is invalid or has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({
            'error': 'invalid_link',
            'message': 'Verification link is invalid'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_password_reset(request):
    """
    Send password reset link
    """
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
        
        # Generate reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        
        # Send email
        subject = 'Reset your Instagran password'
        message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=message,
            fail_silently=False
        )
        
        return Response({
            'message': 'Password reset email sent successfully',
            'email': email
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # Don't reveal if email exists or not
        return Response({
            'message': 'If this email exists in our system, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'email_send_failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request, uidb64, token):
    """
    Reset password using token
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            serializer = SetPasswordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            new_password = serializer.validated_data['new_password']
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password reset successfully',
                'status': 'reset'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'invalid_token',
                'message': 'Reset link is invalid or has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({
            'error': 'invalid_link',
            'message': 'Reset link is invalid'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': 'reset_failed',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password for authenticated user
    """
    try:
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not request.user.check_password(current_password):
            return Response({
                'error': 'invalid_current_password',
                'message': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'error': 'passwords_dont_match',
                'message': 'New passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({
                'error': 'password_too_short',
                'message': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'change_failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_email_exists(request):
    """
    Check if email exists in system
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'email_required',
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(email=email).exists()
    
    return Response({
        'exists': exists,
        'message': 'Email check completed'
    }, status=status.HTTP_200_OK)
