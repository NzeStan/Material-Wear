"""App Configuration"""

from django.apps import AppConfig


class AcademicDirectoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academic_directory'
    verbose_name = 'Academic Directory'
    
    def ready(self):
        """Import signals when app is ready."""
        import academic_directory.signals