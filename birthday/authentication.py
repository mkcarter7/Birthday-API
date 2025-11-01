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
            # Return None instead of raising - let permissions decide
            return None

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
            logger.info("Using FIREBASE_SERVICE_ACCOUNT_JSON")
            return json.loads(svc_json)
        except json.JSONDecodeError:
            logger.error('FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON')
    
    # Option B: Individual fields
    project_id = os.getenv('FIREBASE_PROJECT_ID')
    client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
    private_key = os.getenv('FIREBASE_PRIVATE_KEY')
    
    logger.info(f"_build_service_account_from_env called")
    logger.info(f"Firebase env check: project_id={bool(project_id)}, client_email={bool(client_email)}, private_key={bool(private_key)}")
    
    if project_id and client_email and private_key:
        # Handle escaped newlines in env vars
        private_key = private_key.replace('\\n', '\n')
        logger.info("Building Firebase service account from individual env vars")
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
    logger.warning("No Firebase credentials found in environment")
    return None


def initialize_firebase():
    """
    Initialize Firebase Admin SDK using environment variables when available.
    Fallback to GOOGLE_APPLICATION_CREDENTIALS or default credentials.
    """
    if firebase_admin._apps:
        # Check if the existing app has a project ID
        try:
            app = firebase_admin.get_app()
            # Try to verify the app has project ID by checking options
            if hasattr(app.project_id, '__call__'):
                project_id = app.project_id()
            else:
                project_id = getattr(app, 'project_id', None)
            
            if not project_id:
                logger.warning("Firebase initialized without project ID, attempting to re-initialize...")
                # Delete the existing app and re-initialize
                firebase_admin.delete_app(app)
            else:
                logger.info(f"Firebase already initialized with project: {project_id}")
                return
        except Exception as e:
            logger.warning(f"Error checking existing Firebase app: {e}, attempting re-initialization...")
            try:
                app = firebase_admin.get_app()
                firebase_admin.delete_app(app)
            except:
                pass

    logger.info("Initializing Firebase...")
    try:
        # Get project ID from env var or service account
        project_id = os.getenv('FIREBASE_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
        
        # 1) Try service account from env (JSON or fields)
        svc_dict = _build_service_account_from_env()
        if svc_dict:
            cred = credentials.Certificate(svc_dict)
            # Use project_id from service account or env - MUST have project_id
            app_project_id = svc_dict.get('project_id') or project_id
            if not app_project_id:
                logger.error("Firebase project ID is required but not found in service account or environment")
                raise ValueError("FIREBASE_PROJECT_ID must be set in environment or service account")
            firebase_admin.initialize_app(cred, {'projectId': app_project_id})
            logger.info(f"Firebase initialized successfully from environment variables (project: {app_project_id})")
            return

        # 2) Try GOOGLE_APPLICATION_CREDENTIALS path
        gac_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if gac_path and os.path.exists(gac_path):
            logger.info(f"Using GOOGLE_APPLICATION_CREDENTIALS: {gac_path}")
            cred = credentials.Certificate(gac_path)
            # Try to read project_id from the credentials file
            try:
                import json
                with open(gac_path, 'r') as f:
                    cred_data = json.load(f)
                    file_project_id = cred_data.get('project_id')
            except:
                file_project_id = None
            
            final_project_id = file_project_id or project_id
            if not final_project_id:
                logger.error("Firebase project ID is required but not found in credentials file or environment")
                raise ValueError("FIREBASE_PROJECT_ID must be set in environment or credentials file")
            firebase_admin.initialize_app(cred, {'projectId': final_project_id})
            logger.info(f"Firebase initialized successfully from GOOGLE_APPLICATION_CREDENTIALS (project: {final_project_id})")
            return

        # 3) Try local file if present (optional for dev)
        if os.path.exists('firebase-service-account.json'):
            logger.info("Using local firebase-service-account.json file")
            cred = credentials.Certificate('firebase-service-account.json')
            if project_id:
                firebase_admin.initialize_app(cred, {'projectId': project_id})
            else:
                firebase_admin.initialize_app(cred)
            logger.info(f"Firebase initialized successfully from local file (project: {project_id or 'default'})")
            return

        # 4) Fallback: default credentials with project ID if available
        if project_id:
            logger.warning(f"Using default credentials with project ID: {project_id}")
            firebase_admin.initialize_app({'projectId': project_id})
            logger.info(f"Firebase initialized with default credentials (project: {project_id})")
        else:
            logger.warning("No Firebase credentials found, attempting default initialization")
            firebase_admin.initialize_app()
            logger.info("Firebase initialized with default credentials")
    except Exception as e:
        logger.warning(f"Firebase init attempt failed: {e}")
        try:
            project_id = os.getenv('FIREBASE_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
            if project_id:
                logger.warning(f"Trying default Firebase initialization with project ID: {project_id}")
                firebase_admin.initialize_app({'projectId': project_id})
                logger.info(f"Firebase initialized with default credentials (project: {project_id})")
            else:
                logger.warning("Trying default Firebase initialization as fallback...")
                firebase_admin.initialize_app()
                logger.info("Firebase initialized with default credentials (fallback)")
        except Exception as inner:
            logger.error(f"Firebase initialization completely failed: {inner}")
