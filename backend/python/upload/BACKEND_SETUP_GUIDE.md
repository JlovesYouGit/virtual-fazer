# Backend Upload System Setup Guide

## Overview

Complete backend implementation for the content upload system with permissions, file processing, security, and cloud storage integration.

## Architecture

### Core Components

1. **Upload API** (`views.py`) - RESTful endpoints for file uploads
2. **Models** (`models.py`) - Database models for files, sessions, quotas
3. **Permissions** (`permissions.py`) - Access control and authorization
4. **Processing** (`tasks.py`) - Background file processing with Celery
5. **Utilities** (`utils.py`) - File handling, validation, and processing
6. **Security** - Malware scanning, content moderation, access control

### Key Features

- **Direct Cloud Upload**: Presigned URLs for secure direct uploads
- **File Processing**: Automatic thumbnail generation, compression, filtering
- **Security**: Malware scanning, content moderation, access control
- **Quota Management**: User upload limits and storage quotas
- **Background Processing**: Async processing with Celery
- **Analytics**: Upload statistics and usage tracking

## Installation

### 1. Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Run migrations
python manage.py migrate upload

# Create superuser
python manage.py createsuperuser
```

### 3. Environment Variables

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION=us-east-1

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECRET_KEY=your_django_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

### 4. URL Configuration

Add to your main `urls.py`:

```python
urlpatterns = [
    # ... existing URLs
    path('api/upload/', include('upload.urls')),
]
```

### 5. Settings Configuration

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'upload',
    'rest_framework',
    'corsheaders',
]

# Configure storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
```

## API Endpoints

### Upload Flow

1. **Initialize Upload**
   ```
   POST /api/upload/init/
   ```
   Returns presigned URL for direct upload

2. **Upload File**
   Client uploads directly to cloud storage using presigned URL

3. **Confirm Upload**
   ```
   POST /api/upload/confirm/{file_id}/
   ```
   Triggers backend processing

4. **Check Status**
   ```
   GET /api/upload/status/{file_id}/
   ```
   Returns processing status

### File Management

- **Get File Info**: `GET /api/upload/file/{file_id}/`
- **Delete File**: `DELETE /api/upload/file/{file_id}/delete/`
- **Process File**: `POST /api/upload/file/{file_id}/process/`

### User Management

- **User Uploads**: `GET /api/upload/user-files/`
- **Analytics**: `GET /api/upload/analytics/`

## Security Features

### 1. Authentication & Authorization

```python
# Permission classes
@permission_classes([IsAuthenticated, CanUploadContent])
```

- **CanUploadContent**: Checks user quota and suspension status
- **CanDeleteFile**: Only file owners can delete files
- **CanModerateContent**: Admin and moderator access

### 2. File Validation

- **File Type Validation**: Extension and MIME type checking
- **Size Limits**: Configurable per-user limits
- **Malware Scanning**: ClamAV integration
- **Content Moderation**: AI-powered inappropriate content detection

### 3. Access Control

- **User Quotas**: Daily file limits and storage quotas
- **Ownership**: Users can only access their own files
- **Permission Layers**: Multiple permission checks per operation

## File Processing Pipeline

### 1. Upload Processing

```python
@shared_task
def process_uploaded_file(file_id):
    # 1. Extract metadata
    metadata = get_file_metadata(file_path)
    
    # 2. Generate thumbnail
    generate_thumbnail(file_path, thumbnail_path)
    
    # 3. Scan for malware
    scan_result = scan_file_for_malware(file_path)
    
    # 4. Content moderation
    content_analysis = detect_inappropriate_content(file_path)
    
    # 5. Update database
    uploaded_file.upload_status = 'completed'
```

### 2. Additional Processing

```python
@shared_task
def process_file_with_options(file_id, compress, quality, filters):
    # Apply filters
    for filter_name in filters:
        apply_image_filter(file_path, output_path, filter_name)
    
    # Apply compression
    if compress:
        compress_image(file_path, output_path, quality)
```

## Database Models

### UploadSession
- Tracks upload sessions for direct-to-cloud uploads
- Handles expiration and cleanup
- Stores presigned URLs and metadata

### UploadedFile
- Main file record with metadata
- Processing status and results
- Security scan results
- Analytics data

### UserUploadQuota
- Per-user upload limits
- Storage quotas
- Daily file limits
- Usage tracking

### FileProcessingTask
- Background task tracking
- Progress monitoring
- Error handling
- Result storage

## Celery Tasks

### 1. File Processing
- `process_uploaded_file` - Main processing pipeline
- `process_file_with_options` - Additional processing
- `cleanup_old_uploads` - Expired upload cleanup

### 2. Maintenance
- `update_user_storage_stats` - Quota updates
- `moderate_pending_content` - Content moderation
- `cleanup_old_uploads` - Periodic cleanup

## Cloud Storage Integration

### AWS S3 Setup

```python
# Presigned URL generation
def generate_presigned_url(file_key, content_type, file_size):
    s3_client = boto3.client('s3', ...)
    url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': file_key,
            'ContentType': content_type,
        },
        ExpiresIn=3600
    )
    return url, headers
```

### File Structure
```
uploads/
  {user_id}/
    {file_id}/
      original_file.jpg
      thumbnail.jpg
      processed/
        compressed.jpg
        filtered.jpg
```

## Content Moderation

### 1. Automated Scanning
- **Malware Detection**: ClamAV integration
- **Content Analysis**: AI-powered inappropriate content detection
- **File Validation**: Type and size verification

### 2. Manual Moderation
- **Admin Interface**: Django admin integration
- **Moderation Logs**: Complete audit trail
- **Action Tracking**: All moderation actions logged

### 3. Approval Workflow
```python
# Auto-approve clean content
if scan_result == 'clean' and content_analysis['is_appropriate']:
    uploaded_file.is_approved = True
    ContentModerationLog.objects.create(
        uploaded_file=uploaded_file,
        action='auto_approve',
        reason='Clean scan result'
    )
```

## User Quotas

### Default Limits
- **Daily Files**: 50 files per day
- **Storage**: 1GB total storage
- **File Size**: 100MB per file

### Quota Management
```python
class UserUploadQuota(models.Model):
    max_files_per_day = models.PositiveIntegerField(default=50)
    max_storage_mb = models.PositiveIntegerField(default=1000)
    max_file_size_mb = models.PositiveIntegerField(default=100)
    files_today = models.PositiveIntegerField(default=0)
    storage_used_mb = models.PositiveIntegerField(default=0)
```

### Permission Checks
```python
def can_upload_file(self, file_size_mb):
    if self.files_today >= self.max_files_per_day:
        return False, "Daily file upload limit exceeded"
    if self.storage_used_mb + file_size_mb > self.max_storage_mb:
        return False, "Storage quota exceeded"
    return True, "Upload allowed"
```

## Monitoring & Analytics

### 1. Upload Statistics
- Total uploads per user
- Storage usage tracking
- File type breakdown
- Upload trends over time

### 2. Performance Monitoring
- Processing time tracking
- Error rate monitoring
- Storage performance metrics
- API response times

### 3. Security Monitoring
- Malware detection rates
- Content moderation flags
- Failed upload attempts
- Suspicious activity detection

## Error Handling

### 1. Upload Errors
- **File Size**: Clear error messages for size limits
- **File Type**: Specific type validation errors
- **Network**: Retry logic for connection issues
- **Storage**: Fallback handling for storage issues

### 2. Processing Errors
- **Corruption**: Handle corrupted files gracefully
- **Format**: Unsupported format handling
- **Timeout**: Processing timeout management
- **Resources**: Resource exhaustion handling

### 3. Security Errors
- **Malware**: Immediate quarantine of infected files
- **Content**: Auto-rejection of inappropriate content
- **Permission**: Clear access denied messages
- **Quota**: User-friendly quota exceeded messages

## Performance Optimization

### 1. Direct Upload
- **Presigned URLs**: Direct-to-cloud uploads
- **Chunked Upload**: Large file support
- **Parallel Processing**: Multiple file uploads
- **Background Tasks**: Async processing pipeline

### 2. Caching
- **Metadata Cache**: File metadata caching
- **URL Caching**: Presigned URL caching
- **Thumbnail Cache**: Generated thumbnail caching
- **Quota Cache**: User quota caching

### 3. Database Optimization
- **Indexes**: Optimized database indexes
- **Query Optimization**: Efficient query patterns
- **Connection Pooling**: Database connection management
- **Bulk Operations**: Efficient bulk processing

## Deployment

### 1. Production Settings
```python
# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Performance
USE_TZ = True
TIME_ZONE = 'UTC'

# Storage
AWS_S3_CUSTOM_DOMAIN = f'{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
```

### 2. Celery Configuration
```python
# celery.py
from celery import Celery
from django.conf import settings

app = Celery('upload')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-uploads': {
        'task': 'upload.tasks.cleanup_old_uploads',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

### 3. Monitoring Setup
- **Sentry Integration**: Error tracking
- **Prometheus Metrics**: Performance monitoring
- **Health Checks**: Service health monitoring
- **Log Aggregation**: Centralized logging

## Testing

### 1. Unit Tests
```python
class UploadAPITestCase(TestCase):
    def test_upload_init(self):
        # Test upload initialization
        response = self.client.post('/api/upload/init/', data)
        self.assertEqual(response.status_code, 200)
    
    def test_file_validation(self):
        # Test file validation
        self.assertFalse(validate_file_type('test.txt', 'image'))
```

### 2. Integration Tests
- **End-to-End Upload**: Complete upload flow testing
- **Permission Testing**: Access control validation
- **Processing Testing**: Background task testing
- **Security Testing**: Security feature validation

### 3. Load Testing
- **Concurrent Uploads**: Multiple simultaneous uploads
- **Large Files**: Large file upload testing
- **Storage Performance**: Storage performance testing
- **Database Performance**: Database load testing

## Troubleshooting

### Common Issues

1. **Upload Fails**
   - Check AWS credentials
   - Verify bucket permissions
   - Check file size limits

2. **Processing Stuck**
   - Check Celery worker status
   - Verify task queue health
   - Check storage connectivity

3. **Permission Denied**
   - Verify user authentication
   - Check quota limits
   - Verify user status

### Debug Tools
- **Django Debug Toolbar**: Request debugging
- **Celery Flower**: Task monitoring
- **AWS CloudWatch**: Storage monitoring
- **Sentry**: Error tracking

---

## Usage Examples

### Frontend Integration

```javascript
// Initialize upload
const response = await fetch('/api/upload/init/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    file_type: 'image',
    file_name: file.name,
    file_size: file.size
  })
});

const { file_id, upload_url, headers } = await response.json();

// Upload directly to cloud storage
await fetch(upload_url, {
  method: 'PUT',
  headers: headers,
  body: file
});

// Confirm upload
await fetch(`/api/upload/confirm/${file_id}/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    original_name: file.name,
    mime_type: file.type,
    dimensions: { width: 1920, height: 1080 }
  })
});
```

### Backend Processing

```python
# Process file with filters
from upload.tasks import process_file_with_options

process_file_with_options.delay(
    file_id='uuid-string',
    compress=True,
    quality=0.8,
    filters=['vintage', 'dramatic']
)
```

---

**Status**: Complete backend implementation with full security, permissions, processing pipeline, and cloud storage integration ready for production deployment.
