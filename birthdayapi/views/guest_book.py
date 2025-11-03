from rest_framework import viewsets, status, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..models import GuestBookEntry


class GuestBookEntrySerializer(serializers.ModelSerializer):
    """Serializer for GuestBookEntry model"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_first_name = serializers.CharField(source='author.first_name', read_only=True)
    author_last_name = serializers.CharField(source='author.last_name', read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = GuestBookEntry
        fields = [
            'id', 'party', 'party_name', 'author', 'author_username', 
            'author_first_name', 'author_last_name', 'name', 'message', 
            'created_at', 'updated_at', 'can_edit'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def get_can_edit(self, obj):
        """Check if current user can edit this entry (author or admin)"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Admins can edit any entry, authors can edit their own
            return obj.is_author(request.user) or request.user.is_staff or request.user.is_superuser
        return False


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow authors to edit/delete their own entries,
    or admins (staff/superusers) to edit/delete any entry.
    Everyone can read.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # Write permissions require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins (staff or superuser) can edit/delete any entry
        # Check admin status explicitly
        is_admin = getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
        if is_admin:
            return True
        
        # Write permissions are only allowed to the author of the entry
        return obj.is_author(request.user)


class GuestBookEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing guest book entries.
    
    Core Operations:
    - GET /api/guestbook/ - List all entries (public)
    - GET /api/guestbook/{id}/ - Get single entry (public)
    - POST /api/guestbook/ - Create new entry (authenticated)
    - PUT /api/guestbook/{id}/ - Update entire entry (author or admin)
    - PATCH /api/guestbook/{id}/ - Partial update (author or admin)
    - DELETE /api/guestbook/{id}/ - Delete entry (author or admin)
    - GET /api/guestbook/my_entries/ - Get current user's entries
    """
    serializer_class = GuestBookEntrySerializer
    permission_classes = [IsAuthorOrReadOnly]
    
    def get_permissions(self):
        """
        Override to skip permission check for destroy action.
        We handle permissions manually in destroy() method.
        """
        if self.action == 'destroy':
            # Return empty permissions for destroy - we handle it manually
            return []
        return super().get_permissions()
    
    def check_object_permissions(self, request, obj):
        """
        Override to skip object permission check for destroy action.
        """
        if self.action == 'destroy':
            # Skip - we handle in destroy() method
            return
        return super().check_object_permissions(request, obj)
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to allow admins to delete any entry.
        Handles permissions manually to ensure admin check works correctly.
        """
        instance = self.get_object()
        
        # Check authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get admin status - refresh from database to ensure we have latest
        try:
            from django.contrib.auth.models import User
            db_user = User.objects.get(pk=request.user.pk)
            is_admin = db_user.is_staff or db_user.is_superuser
        except Exception:
            is_admin = getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
        
        # Check if user is the author
        is_author = instance.is_author(request.user)
        
        # Allow deletion if user is admin or author
        if not (is_admin or is_author):
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Perform the deletion
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get_queryset(self):
        """Get guest book entries with optional filtering"""
        queryset = GuestBookEntry.objects.select_related('author', 'party')
        
        # Filter by party (most common use case)
        party_id = self.request.query_params.get('party')
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Search in messages
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(message__icontains=search)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Automatically set the author to current user"""
        serializer.save(author=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_entries(self, request):
        """Get current user's guest book entries"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        entries = GuestBookEntry.objects.filter(author=request.user).select_related('party')
        
        party_id = request.query_params.get('party')
        if party_id:
            entries = entries.filter(party_id=party_id)
        
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)
