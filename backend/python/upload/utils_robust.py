"""
Robust upload utilities with graceful degradation for missing dependencies
"""
import logging
from typing import Optional, Dict, Any
import os
from PIL import Image

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None
    logger.warning("OpenCV not available - image processing will be limited")

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None
    ClientError = None
    logger.warning("Boto3 not available - S3 upload will be disabled")

class RobustImageProcessor:
    """
    Image processing with fallback for missing dependencies
    """
    
    def __init__(self):
        self.available_features = {
            'opencv_processing': HAS_CV2,
            's3_upload': HAS_BOTO3,
            'basic_image_processing': True  # PIL is always available
        }
    
    def process_image(self, image_path: str, max_size: tuple = (1080, 1080)) -> Dict[str, Any]:
        """
        Process image with fallback methods
        """
        result = {
            'success': False,
            'processed_path': None,
            'dimensions': None,
            'file_size': None,
            'processing_method': 'basic'
        }
        
        try:
            # Basic PIL processing (always available)
            with Image.open(image_path) as img:
                original_size = img.size
                result['dimensions'] = original_size
                
                # Resize if needed
                if original_size[0] > max_size[0] or original_size[1] > max_size[1]:
                    img.thumbnail(max_size)
                    result['dimensions'] = img.size
                
                # Save processed image
                processed_path = f"{image_path}_processed.jpg"
                img.save(processed_path, 'JPEG', quality=85)
                result['processed_path'] = processed_path
                result['file_size'] = os.path.getsize(processed_path)
                result['success'] = True
                
                # Try advanced processing if OpenCV is available
                if self.available_features['opencv_processing']:
                    try:
                        cv_result = self._opencv_process(processed_path)
                        if cv_result['success']:
                            result.update(cv_result)
                            result['processing_method'] = 'opencv_enhanced'
                    except Exception as e:
                        logger.warning(f"OpenCV processing failed, using basic: {e}")
                
                return result
                
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return result
    
    def _opencv_process(self, image_path: str) -> Dict[str, Any]:
        """
        Advanced OpenCV processing
        """
        if not HAS_CV2:
            return {'success': False, 'error': 'OpenCV not available'}
        
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return {'success': False, 'error': 'Could not read image with OpenCV'}
            
            # Apply basic enhancements
            enhanced = cv2.convertScaleAbs(img, alpha=1.1, beta=10)
            
            # Save enhanced version
            enhanced_path = f"{image_path}_enhanced.jpg"
            cv2.imwrite(enhanced_path, enhanced)
            
            return {
                'success': True,
                'enhanced_path': enhanced_path,
                'processing_method': 'opencv_enhanced'
            }
            
        except Exception as e:
            logger.error(f"OpenCV processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_to_s3(self, file_path: str, bucket_name: str, object_name: str = None) -> Dict[str, Any]:
        """
        Upload to S3 with fallback
        """
        if not self.available_features['s3_upload']:
            return {
                'success': False,
                'error': 'S3 upload not available - boto3 not installed',
                'fallback': 'local_storage'
            }
        
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        try:
            s3_client = boto3.client('s3')
            
            # Upload file
            s3_client.upload_file(file_path, bucket_name, object_name)
            
            # Generate URL
            url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
            
            return {
                'success': True,
                'url': url,
                'bucket': bucket_name,
                'object_name': object_name
            }
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': 'local_storage'
            }
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': 'local_storage'
            }
    
    def get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Extract image metadata
        """
        metadata = {
            'success': False,
            'format': None,
            'mode': None,
            'size': None,
            'has_exif': False
        }
        
        try:
            with Image.open(image_path) as img:
                metadata.update({
                    'success': True,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'has_exif': hasattr(img, '_getexif') and img._getexif() is not None
                })
                
                # Add EXIF data if available
                if metadata['has_exif']:
                    try:
                        exif = img._getexif()
                        if exif:
                            metadata['exif'] = {str(k): str(v) for k, v in exif.items()[:10]}  # First 10 items
                    except Exception:
                        pass
                
                return metadata
                
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return metadata

# Global processor instance
image_processor = RobustImageProcessor()

def is_image_processing_available() -> bool:
    """Check if image processing is available"""
    return any(image_processor.available_features.values())

def get_available_image_features() -> Dict[str, bool]:
    """Get available image processing features"""
    return image_processor.available_features.copy()
