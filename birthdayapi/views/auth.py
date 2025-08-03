from birthdayapi.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response


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
