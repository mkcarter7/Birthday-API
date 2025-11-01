from birthdayapi.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


@api_view(['POST'])
def check_user(request):
    '''Checks to see if User is Associated 

    Method arguments:
      request -- The full HTTP request object
    '''
    uid = request.data['uid']

    # Use the built-in authenticate method to verify
    # authenticate returns the user object or None if no user is found
    user = User.objects.filter(uid=uid).first()

    # If authentication was successful, respond with their token
    if user is not None:
        data = {
            'uid': user.uid,
            'name': user.name,
            'email': user.email
        }
        return Response(data)
    else:
        # Bad login details were provided. So we can't log the user in.
        data = { 'valid': False }
        return Response(data)


@api_view(['POST'])
def register_user(request):
    '''Handles the creation of a new userr for authentication

    Method arguments:
      request -- The full HTTP request object
    '''

    #save the user info
    user = User.objects.create(
        name=request.data['name'],
        email=request.data['email'],
        uid=request.data['uid']
    )

    # Return the info to the client
    data = {
        'uid': user.uid,
        'name': user.name,
        'email': user.email
    }
    return Response(data)
# In your Django app (e.g., birthday/authentication.py)
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import firebase_admin
from firebase_admin import auth, credentials
import os

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        try:
            id_token = auth_header.split(' ')[1]
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            
            # You can create or get a user based on the Firebase UID
            # For now, we'll just return a tuple indicating successful authentication
            return (None, decoded_token)  # (user, auth)
        except Exception as e:
            raise AuthenticationFailed(f'Invalid Firebase ID token: {str(e)}')
