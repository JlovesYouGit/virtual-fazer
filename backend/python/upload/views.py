from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import uuid
import boto3
import os
from datetime import datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import UploadedFile, UploadSession
from .serializers import UploadedFileSerializer
from .utils import (
    generate_presigned_url,
    validate_file_type,
    get_file_metadata,
    process_uploaded_file,
    scan_file_for_malware
)
from .permissions import CanUploadContent


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanUploadContent])
def initialize_upload(request):
    """
    Initialize upload and generate presigned URL for direct upload to cloud storage
    """
    try:
        data = json.loads(request.body)
        file_type = data.get('file_type')  # 'image' or 'video'
        file_name = data.get('file_name')
        file_size = data.get('file_size')
        
        # Validate input
        if not all([file_type, file_name, file_size]):
            return Response({
                'error': 'Missing required fields: file_type, file_name, file_size'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        if file_type not in ['image', 'video']:
            return Response({
                'error': 'Invalid file type. Must be image or video'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (100MB max)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            return Response({
                'error': f'File size exceeds maximum limit of {max_size // (1024*1024)}MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file extension
        if not validate_file_type(file_name, file_type):
            return Response({
                'error': f'Invalid file extension for {file_type}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Create upload session
        upload_session = UploadSession.objects.create(
            user=request.user,
            file_id=file_id,
            original_name=file_name,
            file_type=file_type,
            file_size=file_size,
            status='initialized'
        )
        
        # Generate presigned URL for direct upload
        file_key = f"uploads/{request.user.id}/{file_id}/{file_name}"
        upload_url, headers = generate_presigned_url(
            file_key=file_key,
            content_type=data.get('content_type', 'application/octet-stream'),
            file_size=file_size
        )
        
        return Response({
            'file_id': file_id,
            'upload_url': upload_url,
            'headers': headers,
            'max_size': max_size,
            'file_key': file_key
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON in request body'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Upload initialization failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanUploadContent])
def confirm_upload(request, file_id):
    """
    Confirm successful upload and trigger backend processing
    """
    try:
        # Get upload session
        try:
            upload_session = UploadSession.objects.get(
                file_id=file_id,
                user=request.user,
                status='initialized'
            )
        except UploadSession.DoesNotExist:
            return Response({
                'error': 'Upload session not found or already processed'
            }, status=status.HTTP_404_NOT_FOUND)
        
        data = json.loads(request.body)
        original_name = data.get('original_name')
        mime_type = data.get('mime_type')
        dimensions = data.get('dimensions', {})
        duration = data.get('duration')
        
        # Create uploaded file record
        uploaded_file = UploadedFile.objects.create(
            user=request.user,
            file_id=file_id,
            original_name=original_name or upload_session.original_name,
            file_type=upload_session.file_type,
            file_size=upload_session.file_size,
            mime_type=mime_type,
            width=dimensions.get('width'),
            height=dimensions.get('height'),
            duration=duration,
            upload_status='pending'
        )
        
        # Update upload session
        upload_session.status = 'completed'
        upload_session.save()
        
        # Trigger async processing
        process_uploaded_file.delay(uploaded_file.id)
        
        return Response(UploadedFileSerializer(uploaded_file).data, status=status.HTTP_201_CREATED)
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON in request body'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Upload confirmation failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_upload_status(request, file_id):
    """
    Get upload status and processing progress
    """
    try:
        uploaded_file = UploadedFile.objects.get(
            file_id=file_id,
            user=request.user
        )
        
        serializer = UploadedFileSerializer(uploaded_file)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except UploadedFile.DoesNotExist:
        return Response({
            'error': 'File not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to get upload status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request, file_id):
    """
    Delete uploaded file and associated storage
    """
    try:
        uploaded_file = UploadedFile.objects.get(
            file_id=file_id,
            user=request.user
        )
        
        # Delete from cloud storage
        if uploaded_file.file_path:
            try:
                default_storage.delete(uploaded_file.file_path)
            except Exception as e:
                # Log error but continue with database deletion
                print(f"Failed to delete file from storage: {e}")
        
        # Delete thumbnail
        if uploaded_file.thumbnail_path:
            try:
                default_storage.delete(uploaded_file.thumbnail_path)
            except Exception as e:
                print(f"Failed to delete thumbnail from storage: {e}")
        
        # Delete database record
        uploaded_file.delete()
        
        return Response({
            'message': 'File deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except UploadedFile.DoesNotExist:
        return Response({
            'error': 'File not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to delete file: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_file_info(request, file_id):
    """
    Get detailed file information
    """
    try:
        uploaded_file = UploadedFile.objects.get(
            file_id=file_id,
            user=request.user
        )
        
        serializer = UploadedFileSerializer(uploaded_file)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except UploadedFile.DoesNotExist:
        return Response({
            'error': 'File not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to get file info: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanUploadContent])
def process_file(request, file_id):
    """
    Apply additional processing to uploaded file (filters, compression, etc.)
    """
    try:
        uploaded_file = UploadedFile.objects.get(
            file_id=file_id,
            user=request.user
        )
        
        if uploaded_file.upload_status != 'completed':
            return Response({
                'error': 'File must be fully uploaded before processing'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = json.loads(request.body)
        compress = data.get('compress', False)
        quality = data.get('quality', 0.8)
        filters = data.get('filters', [])
        format_type = data.get('format')
        
        # Trigger async processing with options
        from .tasks import process_file_with_options
        process_file_with_options.delay(
            file_id=uploaded_file.id,
            compress=compress,
            quality=quality,
            filters=filters,
            format_type=format_type
        )
        
        # Update status
        uploaded_file.upload_status = 'processing'
        uploaded_file.save()
        
        return Response({
            'message': 'File processing started',
            'file_id': file_id
        }, status=status.HTTP_202_ACCEPTED)
        
    except UploadedFile.DoesNotExist:
        return Response({
            'error': 'File not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to start file processing: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_uploads(request):
    """
    Get paginated list of user's uploaded files
    """
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        file_type = request.GET.get('file_type')
        upload_status = request.GET.get('upload_status')
        
        # Build queryset
        queryset = UploadedFile.objects.filter(user=request.user)
        
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        if upload_status:
            queryset = queryset.filter(upload_status=upload_status)
        
        # Order by creation date (newest first)
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        offset = (page - 1) * limit
        files = queryset[offset:offset + limit]
        total_count = queryset.count()
        
        serializer = UploadedFileSerializer(files, many=True)
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'next': f"/api/upload/user-files/?page={page + 1}" if offset + limit < total_count else None,
            'previous': f"/api/upload/user-files/?page={page - 1}" if page > 1 else None
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get user uploads: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_upload_analytics(request):
    """
    Get upload analytics for the current user
    """
    try:
        user_files = UploadedFile.objects.filter(user=request.user)
        
        # Basic stats
        total_uploads = user_files.count()
        total_size = sum(f.file_size for f in user_files)
        
        # File type breakdown
        images_count = user_files.filter(file_type='image').count()
        videos_count = user_files.filter(file_type='video').count()
        
        # Upload trends (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_uploads = user_files.filter(created_at__gte=thirty_days_ago)
        
        # Group by date
        upload_trends = {}
        for file in recent_uploads:
            date_str = file.created_at.strftime('%Y-%m-%d')
            upload_trends[date_str] = upload_trends.get(date_str, 0) + 1
        
        # Convert to list format
        trends_list = [
            {'date': date, 'count': count}
            for date, count in sorted(upload_trends.items())
        ]
        
        return Response({
            'total_uploads': total_uploads,
            'total_size': total_size,
            'file_type_breakdown': {
                'images': images_count,
                'videos': videos_count
            },
            'upload_trends': trends_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get upload analytics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(['POST'])
def webhook_upload_complete(request):
    """
    Webhook endpoint for cloud storage upload completion notifications
    """
    try:
        # Verify webhook signature (if applicable)
        signature = request.headers.get('X-Signature')
        if not verify_webhook_signature(request.body, signature):
            return HttpResponse('Invalid signature', status=401)
        
        data = json.loads(request.body)
        file_id = data.get('file_id')
        status = data.get('status')  # 'success' or 'error'
        
        # Find upload session
        try:
            upload_session = UploadSession.objects.get(file_id=file_id)
        except UploadSession.DoesNotExist:
            return HttpResponse('Upload session not found', status=404)
        
        # Update status based on webhook
        if status == 'success':
            upload_session.status = 'uploaded'
        else:
            upload_session.status = 'failed'
            upload_session.error_message = data.get('error', 'Unknown error')
        
        upload_session.save()
        
        return HttpResponse('Webhook processed', status=200)
        
    except Exception as e:
        print(f"Webhook processing error: {e}")
        return HttpResponse('Webhook processing failed', status=500)


def verify_webhook_signature(payload, signature):
    """
    Verify webhook signature for security
    """
    # Implement signature verification logic
    # This would depend on your cloud storage provider's webhook signing method
    return True  # Placeholder implementation
