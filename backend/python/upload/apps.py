from django.apps import AppConfig


class UploadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'upload'
    verbose_name = 'File Upload System'
    
    def ready(self):
        # Import signals
        from . import signals
