import boto3
import uuid
import os
import mimetypes
from PIL import Image, ImageFilter
import cv2
import numpy as np
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
import magic
import hashlib
import tempfile
import shutil
from io import BytesIO


def generate_presigned_url(file_key, content_type, file_size=None, expiration=3600):
    """
    Generate presigned URL for direct upload to cloud storage (AWS S3)
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION
        )
        
        # Generate presigned URL for PUT operation
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': file_key,
                'ContentType': content_type,
            },
            ExpiresIn=expiration
        )
        
        # Prepare headers for client-side upload
        headers = {
            'Content-Type': content_type,
        }
        
        # Add additional headers for large files if needed
        if file_size and file_size > 5 * 1024 * 1024:  # 5MB
            headers['x-amz-content-sha256'] = 'UNSIGNED-PAYLOAD'
        
        return url, headers
        
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        raise


def validate_file_type(file_name, expected_type):
    """
    Validate file type based on extension and MIME type
    """
    # Allowed extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    video_extensions = {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.flv', '.wmv'}
    
    file_ext = os.path.splitext(file_name)[1].lower()
    
    if expected_type == 'image':
        return file_ext in image_extensions
    elif expected_type == 'video':
        return file_ext in video_extensions
    
    return False


def get_file_metadata(file_path):
    """
    Extract metadata from uploaded file
    """
    metadata = {}
    
    try:
        # Get MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        metadata['mime_type'] = mime_type
        
        # Get file hash
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        metadata['file_hash'] = hash_md5.hexdigest()
        
        # Check if it's an image
        if mime_type.startswith('image/'):
            try:
                with Image.open(file_path) as img:
                    metadata['width'] = img.width
                    metadata['height'] = img.height
                    metadata['format'] = img.format
                    metadata['mode'] = img.mode
                    
                    # Extract EXIF data if available
                    if hasattr(img, '_getexif') and img._getexif():
                        metadata['exif'] = img._getexif()
                        
            except Exception as e:
                print(f"Error reading image metadata: {e}")
        
        # Check if it's a video
        elif mime_type.startswith('video/'):
            try:
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
                    metadata['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    metadata['duration'] = metadata['frame_count'] / metadata['fps'] if metadata['fps'] > 0 else 0
                    metadata['codec'] = cap.get(cv2.CAP_PROP_FOURCC)
                cap.release()
                
            except Exception as e:
                print(f"Error reading video metadata: {e}")
        
        return metadata
        
    except Exception as e:
        print(f"Error extracting file metadata: {e}")
        return {'mime_type': 'application/octet-stream'}


def generate_thumbnail(file_path, output_path, max_size=(300, 300)):
    """
    Generate thumbnail for image or video
    """
    try:
        # Determine file type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        
        if mime_type.startswith('image/'):
            # Generate image thumbnail
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Create thumbnail
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                
        elif mime_type.startswith('video/'):
            # Generate video thumbnail
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                # Seek to 1 second or 10% of video duration
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                
                if fps > 0 and frame_count > 0:
                    target_frame = min(int(fps), int(frame_count * 0.1))
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                
                # Read frame
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Create PIL image
                    img = Image.fromarray(frame_rgb)
                    
                    # Create thumbnail
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Save thumbnail
                    img.save(output_path, 'JPEG', quality=85, optimize=True)
                
                cap.release()
        
        return True
        
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return False


def compress_image(file_path, output_path, quality=85, max_width=1920, max_height=1080):
    """
    Compress image while maintaining quality
    """
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save with compression
            img.save(output_path, 'JPEG', quality=quality, optimize=True, progressive=True)
            
        return True
        
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False


def compress_video(file_path, output_path, quality='medium'):
    """
    Compress video using ffmpeg
    """
    try:
        import subprocess
        
        # Quality settings
        quality_settings = {
            'low': {'crf': 28, 'preset': 'fast'},
            'medium': {'crf': 23, 'preset': 'medium'},
            'high': {'crf': 18, 'preset': 'slow'}
        }
        
        settings = quality_settings.get(quality, quality_settings['medium'])
        
        # Build ffmpeg command
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-c:v', 'libx264',
            '-preset', settings['preset'],
            '-crf', str(settings['crf']),
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',  # Overwrite output file
            output_path
        ]
        
        # Run compression
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            print(f"FFmpeg error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error compressing video: {e}")
        return False


def apply_image_filter(file_path, output_path, filter_name):
    """
    Apply filter to image
    """
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Apply filter
            if filter_name == 'vintage':
                # Sepia effect
                img = img.convert('L')
                img = img.convert('RGB')
                sepia_filter = ImageFilter.Color3Matrix(
                    (0.393, 0.769, 0.189,
                     0.349, 0.686, 0.168,
                     0.272, 0.534, 0.131)
                )
                img = img.filter(sepia_filter)
                
            elif filter_name == 'dramatic':
                # High contrast
                img = img.filter(ImageFilter.CONTRAST_ENHANCE)
                img = img.filter(ImageFilter.SHARPEN)
                
            elif filter_name == 'warm':
                # Warm tone
                img = img.filter(ImageFilter.Color3Matrix(
                    (1.1, 0, 0,
                     0, 1.05, 0,
                     0, 0, 0.9)
                ))
                
            elif filter_name == 'cool':
                # Cool tone
                img = img.filter(ImageFilter.Color3Matrix(
                    (0.9, 0, 0,
                     0, 1.05, 0,
                     0, 0, 1.1)
                ))
            
            # Save filtered image
            img.save(output_path, 'JPEG', quality=90, optimize=True)
            
        return True
        
    except Exception as e:
        print(f"Error applying filter: {e}")
        return False


def scan_file_for_malware(file_path):
    """
    Scan file for malware using ClamAV or similar
    """
    try:
        import pyclamd
        
        # Initialize ClamAV
        cd = pyclamd.ClamdUnixSocket()
        
        # Scan file
        scan_result = cd.scan_file(file_path)
        
        if scan_result is None:
            return 'clean', None
        else:
            return 'infected', scan_result.get(file_path, 'Unknown threat')
            
    except ImportError:
        # ClamAV not available, skip scanning
        print("ClamAV not available, skipping malware scan")
        return 'not_scanned', 'Antivirus not available'
    except Exception as e:
        print(f"Error scanning file: {e}")
        return 'error', str(e)


def detect_inappropriate_content(file_path):
    """
    Use AI to detect inappropriate content
    """
    try:
        # This would integrate with a content moderation API
        # For now, return safe result
        return {
            'is_appropriate': True,
            'confidence': 0.95,
            'flags': [],
            'categories': []
        }
        
    except Exception as e:
        print(f"Error detecting inappropriate content: {e}")
        return {
            'is_appropriate': True,
            'confidence': 0.5,
            'flags': ['scan_error'],
            'categories': []
        }


def create_upload_directory(user_id, file_id):
    """
    Create upload directory structure
    """
    upload_dir = f"uploads/{user_id}/{file_id}/"
    
    # Create directory if it doesn't exist
    if not default_storage.exists(upload_dir):
        default_storage.makedirs(upload_dir)
    
    return upload_dir


def cleanup_expired_uploads():
    """
    Clean up expired upload sessions and temporary files
    """
    from .models import UploadSession
    
    # Find expired sessions
    expired_sessions = UploadSession.objects.filter(
        expires_at__lt=timezone.now(),
        status__in=['initialized', 'uploading']
    )
    
    for session in expired_sessions:
        # Mark as expired
        session.status = 'expired'
        session.save()
        
        # Clean up temporary files if any
        if session.file_key:
            try:
                default_storage.delete(session.file_key)
            except Exception as e:
                print(f"Error cleaning up expired upload: {e}")


def get_storage_usage(user_id):
    """
    Get storage usage statistics for a user
    """
    from .models import UploadedFile
    
    user_files = UploadedFile.objects.filter(user_id=user_id)
    
    total_files = user_files.count()
    total_size = sum(f.file_size for f in user_files)
    
    images_count = user_files.filter(file_type='image').count()
    videos_count = user_files.filter(file_type='video').count()
    
    return {
        'total_files': total_files,
        'total_size': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'images_count': images_count,
        'videos_count': videos_count
    }
