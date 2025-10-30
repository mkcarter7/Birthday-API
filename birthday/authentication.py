import firebase_admin
from firebase_admin import auth, credentials
from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from django.conf import settings
import logging
import json
import os

logger = logging.getLogger(__name__)

class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for Firebase
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        id_token = auth_header.split(' ')[1]
        
        try:
            # Ensure Firebase Admin is initialized (on-demand init)
            if not firebase_admin._apps:
                initialize_firebase()
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            
            # Get or create the user
            user, created = self.get_or_create_user(uid, decoded_token)
            
            return (user, None)
            
        except Exception as e:
            logger.error(f"Firebase authentication error: {str(e)}")
            raise exceptions.AuthenticationFailed('Invalid Firebase token')

    def get_or_create_user(self, uid, decoded_token):
        """
        Get or create a Django user based on Firebase UID
        """
        try:
            # Try to get existing user by username (using UID)
            user = User.objects.get(username=uid)
            return user, False
        except User.DoesNotExist:
            # Create new user
            email = decoded_token.get('email', '')
            name = decoded_token.get('name', '')
            first_name = ''
            last_name = ''
            
            if name:
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                if len(name_parts) > 1:
                    last_name = name_parts[1]
            
            user = User.objects.create_user(
                username=uid,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            return user, True

def _build_service_account_from_env():
    """Return a service account dict built from environment variables or None."""
    # Option A: Entire JSON in one var
    svc_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    if svc_json:
        try:
            return json.loads(svc_json)
        except json.JSONDecodeError:
            logger.error('FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON')
    
    # Option B: Individual fields
    project_id = os.getenv('FIREBASE_PROJECT_ID')
    client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
    private_key = os.getenv('FIREBASE_PRIVATE_KEY')
    if project_id and client_email and private_key:
        # Handle escaped newlines in env vars
        private_key = private_key.replace('\\n', '\n')
        return {
            'type': 'service_account',
            'project_id': project_id,
            'private_key_id': os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
            'private_key': private_key,
            'client_email': client_email,
            'client_id': os.getenv('FIREBASE_CLIENT_ID', ''),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': os.getenv('FIREBASE_CLIENT_X509_CERT_URL', ''),
        }
    return None


def initialize_firebase():
    """
    Initialize Firebase Admin SDK using environment variables when available.
    Fallback to GOOGLE_APPLICATION_CREDENTIALS or default credentials.
    """
    if firebase_admin._apps:
        return

    try:
        # 1) Try service account from env (JSON or fields)
        svc_dict = _build_service_account_from_env()
        if svc_dict:
            cred = credentials.Certificate(svc_dict)
            firebase_admin.initialize_app(cred)
            return

        # 2) Try GOOGLE_APPLICATION_CREDENTIALS path
        gac_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if gac_path and os.path.exists(gac_path):
            cred = credentials.Certificate(gac_path)
            firebase_admin.initialize_app(cred)
            return

        # 3) Try local file if present (optional for dev)
        if os.path.exists('firebase-service-account.json'):
            cred = credentials.Certificate('firebase-service-account.json')
            firebase_admin.initialize_app(cred)
            return

        # 4) Fallback: default credentials (works on GCP or configured envs)
        firebase_admin.initialize_app()
    except Exception as e:
        logger.warning(f"Firebase init fallback: {e}. Using default initialization.")
        try:
            firebase_admin.initialize_app()
        except Exception as inner:
            logger.error(f"Firebase initialization failed: {inner}")
