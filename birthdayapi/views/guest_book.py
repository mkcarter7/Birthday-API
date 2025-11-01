from rest_framework import viewsets, status, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
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
        """Check if current user can edit this entry"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_author(request.user)
        return False


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors to edit/delete their own entries.
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
        
        # Write permissions are only allowed to the author of the entry
        return obj.is_author(request.user)


class GuestBookEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing guest book entries.
    
    Core Operations:
    - GET /api/guestbook/ - List all entries (public)
    - GET /api/guestbook/{id}/ - Get single entry (public)
    - POST /api/guestbook/ - Create new entry (authenticated)
    - PUT /api/guestbook/{id}/ - Update entire entry (author only)
    - PATCH /api/guestbook/{id}/ - Partial update (author only)
    - DELETE /api/guestbook/{id}/ - Delete entry (author only)
    - GET /api/guestbook/my_entries/ - Get current user's entries
    """
    serializer_class = GuestBookEntrySerializer
    permission_classes = [IsAuthorOrReadOnly]
    
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
