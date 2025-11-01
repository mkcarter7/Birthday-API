"""
Admin-related views for checking user permissions and status
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_admin_status(request):
    """
    Check if the current user is an admin/staff member.
    
    Returns:
    - is_admin: True if user is staff or superuser
    - is_staff: User's staff status
    - is_superuser: User's superuser status
    - username: User's username
    - email: User's email
    """
    user = request.user
    return Response({
        'is_admin': user.is_staff or user.is_superuser,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'username': user.username,
        'email': user.email if hasattr(user, 'email') else None,
    })
