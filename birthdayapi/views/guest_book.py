from rest_framework import viewsets, status, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from ..models import GuestBookEntry, Party


class GuestBookEntrySerializer(serializers.ModelSerializer):
    """Serializer for GuestBookEntry model"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_first_name = serializers.CharField(source='author.first_name', read_only=True)
    author_last_name = serializers.CharField(source='author.last_name', read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    party_date = serializers.DateTimeField(source='party.date', read_only=True)
    word_count = serializers.SerializerMethodField()
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = GuestBookEntry
        fields = [
            'id', 'party', 'party_name', 'party_date', 'author', 'author_username', 
            'author_first_name', 'author_last_name', 'message', 'is_featured', 
            'created_at', 'word_count', 'time_since_created'
        ]
        read_only_fields = ['author', 'created_at']
    
    def get_word_count(self, obj):
        """Get word count of the message"""
        return len(obj.message.split()) if obj.message else 0
    
    def get_time_since_created(self, obj):
        """Get human-readable time since creation"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class GuestBookEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing guest book entries
    Users can create, read, and update their own entries
    Only admins can feature/unfeature entries and delete any entry
    """
    serializer_class = GuestBookEntrySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get guest book entries with filtering"""
        queryset = GuestBookEntry.objects.select_related('author', 'party')
        
        # Filter by party (most common use case)
        party_id = self.request.query_params.get('party')
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Filter by author
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Filter by featured status
        is_featured = self.request.query_params.get('featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        
        # Search in messages
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(message__icontains=search)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-is_featured', '-created_at')
    
    def perform_create(self, serializer):
        """Automatically set the author to current user"""
        serializer.save(author=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Override update to check permissions"""
        instance = self.get_object()
        
        # Only allow author or staff to update the entry
        if instance.author != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only update your own guest book entries.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only staff can change featured status
        if 'is_featured' in request.data and not request.user.is_staff:
            request.data.pop('is_featured')
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check permissions"""
        instance = self.get_object()
        
        # Only allow author or staff to delete
        if instance.author != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only delete your own guest book entries.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_entries(self, request):
        """Get current user's guest book entries"""
        entries = GuestBookEntry.objects.filter(author=request.user).select_related('party')
        
        party_id = request.query_params.get('party')
        if party_id:
            entries = entries.filter(party_id=party_id)
        
        serializer = self.get_serializer(entries, many=True)
        
        # Group entries by party
        entries_by_party = {}
        for entry_data in serializer.data:
            party_name = entry_data['party_name']
            if party_name not in entries_by_party:
                entries_by_party[party_name] = []
            entries_by_party[party_name].append(entry_data)
        
        return Response({
            'total_entries': entries.count(),
            'entries_by_party': entries_by_party,
            'all_entries': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured guest book entries"""
        party_id = request.query_params.get('party')
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        queryset = GuestBookEntry.objects.filter(is_featured=True).select_related('author', 'party')
        
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        featured_entries = queryset[:limit]
        serializer = self.get_serializer(featured_entries, many=True)
        
        return Response({
            'featured_entries': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_featured(self, request, pk=None):
        """Toggle featured status of a guest book entry (admin only)"""
        entry = self.get_object()
        entry.is_featured = not entry.is_featured
        entry.save()
        
        serializer = self.get_serializer(entry)
        
        return Response({
            'message': f'Entry {"featured" if entry.is_featured else "unfeatured"} successfully',
            'entry': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def party_stats(self, request):
        """Get statistics for guest book entries in a party"""
        party_id = request.query_params.get('party')
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            party = Party.objects.get(pk=party_id)
            entries = GuestBookEntry.objects.filter(party=party)
            
            if not entries.exists():
                return Response({
                    'party': {
                        'id': party.id,
                        'name': party.name
                    },
                    'stats': {
                        'total_entries': 0,
                        'featured_entries': 0,
                        'unique_authors': 0,
                        'average_word_count': 0,
                        'latest_entry': None
                    },
                    'top_contributors': []
                })
            
            # Calculate statistics
            total_entries = entries.count()
            featured_entries = entries.filter(is_featured=True).count()
            unique_authors = entries.values('author').distinct().count()
            
            # Calculate average word count
            total_words = sum(len(entry.message.split()) for entry in entries)
            avg_word_count = round(total_words / total_entries, 1) if total_entries > 0 else 0
            
            # Get latest entry
            latest_entry = entries.first()
            latest_entry_data = None
            if latest_entry:
                latest_entry_data = {
                    'id': latest_entry.id,
                    'author': latest_entry.author.username,
                    'message_preview': latest_entry.message[:100] + '...' if len(latest_entry.message) > 100 else latest_entry.message,
                    'created_at': latest_entry.created_at
                }
            
            # Get top contributors
            top_contributors = entries.values(
                'author__id', 'author__username', 'author__first_name', 'author__last_name'
            ).annotate(
                entry_count=Count('id')
            ).order_by('-entry_count')[:5]
            
            return Response({
                'party': {
                    'id': party.id,
                    'name': party.name
                },
                'stats': {
                    'total_entries': total_entries,
                    'featured_entries': featured_entries,
                    'unique_authors': unique_authors,
                    'average_word_count': avg_word_count,
                    'latest_entry': latest_entry_data
                },
                'top_contributors': list(top_contributors)
            })
            
        except Party.DoesNotExist:
            return Response(
                {'error': 'Party not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent guest book entries across all parties or specific party"""
        party_id = request.query_params.get('party')
        limit = min(int(request.query_params.get('limit', 20)), 100)
        hours = int(request.query_params.get('hours', 24))  # Default to last 24 hours
        
        # Calculate time threshold
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        queryset = GuestBookEntry.objects.filter(
            created_at__gte=time_threshold
        ).select_related('author', 'party')
        
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        recent_entries = queryset[:limit]
        serializer = self.get_serializer(recent_entries, many=True)
        
        return Response({
            'recent_entries': serializer.data,
            'time_window': f'Last {hours} hours',
            'count': queryset.count()
        })
    
    @action(detail=False, methods=['get'])
    def word_cloud_data(self, request):
        """Get word frequency data for creating word clouds"""
        party_id = request.query_params.get('party')
        
        queryset = GuestBookEntry.objects.all()
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Combine all messages
        all_messages = ' '.join(entry.message.lower() for entry in queryset)
        
        # Simple word frequency count (you might want to use more sophisticated text processing)
        import re
        from collections import Counter
        
        # Remove punctuation and split into words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_messages)  # Only words with 3+ letters
        
        # Common stop words to exclude
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'that', 'with',
            'have', 'this', 'will', 'your', 'from', 'they', 'know', 'want', 'been',
            'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just',
            'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them',
            'well', 'were'
        }
        
        # Filter out stop words and count
        filtered_words = [word for word in words if word not in stop_words]
        word_freq = Counter(filtered_words)
        
        # Get top 50 words
        top_words = word_freq.most_common(50)
        
        return Response({
            'word_frequency': [{'word': word, 'count': count} for word, count in top_words],
            'total_entries': queryset.count(),
            'total_words': len(words),
            'unique_words': len(set(words))
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple guest book entries at once"""
        entries_data = request.data.get('entries', [])
        
        if not entries_data or not isinstance(entries_data, list):
            return Response(
                {'error': 'Entries data must be a non-empty list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_entries = []
        errors = []
        
        for i, entry_data in enumerate(entries_data):
            # Set author to current user
            entry_data['author'] = request.user.id
            
            serializer = self.get_serializer(data=entry_data)
            if serializer.is_valid():
                entry = serializer.save(author=request.user)
                created_entries.append(entry)
            else:
                errors.append({
                    'index': i,
                    'errors': serializer.errors,
                    'data': entry_data
                })
        
        response_data = {
            'created_count': len(created_entries),
            'error_count': len(errors),
            'created_entries': self.get_serializer(created_entries, many=True).data
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)
