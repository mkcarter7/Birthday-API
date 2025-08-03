from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Avg, Max, Count
from django.contrib.auth.models import User
from ..models import GameScore, Party


class GameScoreSerializer(serializers.ModelSerializer):
    """Serializer for GameScore model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    calculated_level = serializers.SerializerMethodField()
    
    class Meta:
        model = GameScore
        fields = [
            'id', 'user', 'user_username', 'user_first_name', 'user_last_name',
            'party', 'party_name', 'total_points', 'level', 'calculated_level', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'level', 'created_at', 'updated_at']
    
    def get_calculated_level(self, obj):
        """Get the calculated level based on current points"""
        return obj.calculate_level()


class GameScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing game scores
    Provides CRUD operations and additional endpoints for leaderboards and stats
    """
    serializer_class = GameScoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = GameScore.objects.select_related('user', 'party')
        
        # Regular users can only see their own scores, staff can see all
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by party if specified
        party_id = self.request.query_params.get('party', None)
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(party__name__icontains=search)
            )
        
        return queryset.order_by('-total_points')
    
    def perform_create(self, serializer):
        """Automatically set the user and calculate level on creation"""
        instance = serializer.save(user=self.request.user)
        instance.level = instance.calculate_level()
        instance.save()
    
    def perform_update(self, serializer):
        """Recalculate level on update"""
        instance = serializer.save()
        instance.level = instance.calculate_level()
        instance.save()
    
    def update(self, request, *args, **kwargs):
        """Override update to check permissions"""
        instance = self.get_object()
        
        # Only allow owner or staff to update
        if instance.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only update your own scores.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check permissions"""
        instance = self.get_object()
        
        # Only allow owner or staff to delete
        if instance.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only delete your own scores.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_scores(self, request):
        """Get current user's game scores across all parties"""
        scores = GameScore.objects.filter(user=request.user).select_related('party')
        
        # Calculate total points
        total_points = scores.aggregate(Sum('total_points'))['total_points__sum'] or 0
        
        serializer = self.get_serializer(scores, many=True)
        
        return Response({
            'scores': serializer.data,
            'total_points': total_points,
            'total_parties': scores.count()
        })
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get leaderboard for a specific party or overall"""
        party_id = request.query_params.get('party')
        limit = min(int(request.query_params.get('limit', 50)), 100)  # Max 100
        
        if party_id:
            # Party-specific leaderboard
            try:
                party = Party.objects.get(pk=party_id)
                scores = GameScore.objects.filter(party=party).select_related('user').order_by('-total_points')[:limit]
                
                serializer = self.get_serializer(scores, many=True)
                
                return Response({
                    'party': {
                        'id': party.id,
                        'name': party.name
                    },
                    'leaderboard': serializer.data,
                    'type': 'party'
                })
            except Party.DoesNotExist:
                return Response(
                    {'error': 'Party not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Overall leaderboard (sum of all user's scores)
            leaderboard = GameScore.objects.values(
                'user__id', 'user__username', 'user__first_name', 'user__last_name'
            ).annotate(
                total_score=Sum('total_points'),
                parties_count=Count('party', distinct=True),
                highest_level=Max('level')
            ).order_by('-total_score')[:limit]
            
            return Response({
                'leaderboard': list(leaderboard),
                'type': 'overall'
            })
    
    @action(detail=True, methods=['post'])
    def add_points(self, request, pk=None):
        """Add points to a specific game score"""
        score = self.get_object()
        
        # Only allow owner or staff to add points
        if score.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only add points to your own scores.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            points_to_add = int(request.data.get('points', 0))
            if points_to_add <= 0:
                return Response(
                    {'error': 'Points must be a positive integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add points and recalculate level
            score.total_points += points_to_add
            score.level = score.calculate_level()
            score.save()
            
            serializer = self.get_serializer(score)
            
            return Response({
                'message': f'Added {points_to_add} points successfully!',
                'points_added': points_to_add,
                'score': serializer.data
            })
            
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid points value. Must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def ranking(self, request, pk=None):
        """Get the ranking of a specific score within its party"""
        score = self.get_object()
        
        # Count scores higher than this one in the same party
        higher_scores = GameScore.objects.filter(
            party=score.party,
            total_points__gt=score.total_points
        ).count()
        
        # Total players in the party
        total_players = GameScore.objects.filter(party=score.party).count()
        
        ranking = higher_scores + 1
        
        return Response({
            'ranking': ranking,
            'total_players': total_players,
            'party': {
                'id': score.party.id,
                'name': score.party.name
            },
            'score': {
                'total_points': score.total_points,
                'level': score.level
            }
        })
    
    @action(detail=False, methods=['get'], url_path='party/(?P<party_id>[0-9]+)/stats')
    def party_stats(self, request, party_id=None):
        """Get comprehensive statistics for a specific party"""
        try:
            party = Party.objects.get(pk=party_id)
            scores = GameScore.objects.filter(party=party)
            
            if not scores.exists():
                return Response({
                    'party': {
                        'id': party.id,
                        'name': party.name
                    },
                    'stats': {
                        'total_players': 0,
                        'average_score': 0,
                        'highest_score': 0,
                        'lowest_score': 0,
                        'total_points': 0,
                        'average_level': 0,
                        'highest_level': 0
                    },
                    'top_players': []
                })
            
            # Calculate statistics
            from django.db.models import Min
            stats = scores.aggregate(
                total_players=Count('id'),
                average_score=Avg('total_points'),
                highest_score=Max('total_points'),
                lowest_score=Min('total_points'),
                total_points=Sum('total_points'),
                average_level=Avg('level'),
                highest_level=Max('level')
            )
            
            # Get top 10 players
            top_players = scores.select_related('user').order_by('-total_points')[:10]
            top_players_data = []
            
            for i, score in enumerate(top_players, 1):
                top_players_data.append({
                    'rank': i,
                    'user': {
                        'id': score.user.id,
                        'username': score.user.username,
                        'first_name': score.user.first_name,
                        'last_name': score.user.last_name
                    },
                    'total_points': score.total_points,
                    'level': score.level
                })
            
            return Response({
                'party': {
                    'id': party.id,
                    'name': party.name
                },
                'stats': {
                    'total_players': stats['total_players'],
                    'average_score': round(stats['average_score'] or 0, 2),
                    'highest_score': stats['highest_score'] or 0,
                    'lowest_score': stats['lowest_score'] or 0,
                    'total_points': stats['total_points'] or 0,
                    'average_level': round(stats['average_level'] or 0, 2),
                    'highest_level': stats['highest_level'] or 0
                },
                'top_players': top_players_data
            })
            
        except Party.DoesNotExist:
            return Response(
                {'error': 'Party not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def level_distribution(self, request):
        """Get distribution of players by level across all parties or specific party"""
        party_id = request.query_params.get('party')
        
        queryset = GameScore.objects.all()
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Group by level and count
        from django.db.models import Count
        distribution = queryset.values('level').annotate(
            count=Count('id')
        ).order_by('level')
        
        return Response({
            'distribution': list(distribution),
            'party_id': party_id
        })
