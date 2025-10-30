from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class BirthdayApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'birthdayapi'
    
    def ready(self):
        """Initialize Firebase when Django is fully loaded"""
        try:
            from birthday.authentication import initialize_firebase
            initialize_firebase()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.warning(f"Firebase initialization skipped: {e}")
