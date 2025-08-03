from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from ..models import GameScore, Badge, UserBadge, Party
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'icon', 'points_required', 
            'color', 'is_active'
        ]

class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ['id', 'user', 'badge', 'party', 'party_name', 'earned_at']

class GameScoreSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    badges = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    
    class Meta:
        model = GameScore
        fields = [
            'id', 'user', 'party', 'party_name', 'total_points', 'level',
            'created_at', 'updated_at', 'badges', 'rank'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'level']
    
    def get_badges(self, obj):
        badges = UserBadge.objects.filter(
            user=obj.user, 
            party=obj.party
        ).select_related('badge')
        return UserBadgeSerializer(badges, many=True).data
    
    def get_rank(self, obj):
        # Get rank within the party
        higher_scores = GameScore.objects.filter(
            party=obj.party,
            total_points__gt=obj.total_points
        ).count()
        return higher_scores + 1

class GameScoreUpdateSerializer(serializers.ModelSerializer):
    points_to_add = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = GameScore
        fields = ['total_points', 'points_to_add']
    
    def validate_points_to_add(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Points to add cannot be negative.")
        return value

class LeaderboardSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user = UserSerializer()
    total_points = serializers.IntegerField()
    level = serializers.IntegerField()
    badge_count = serializers.IntegerField()

class GameScoreViewSet(viewsets.ModelViewSet):
    serializer_class = GameScoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = GameScore.objects.all()
        
        # Filter by party if specified
        party_id = self.request.query_params.get('party')
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by current user's scores
        my_scores = self.request.query_params.get('my_scores')
        if my_scores and my_scores.lower() == 'true':
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.select_related('user', 'party')
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return GameScoreUpdateSerializer
        return GameScoreSerializer
    
    def create(self, request, *args, **kwargs):
        party_id = request.data.get('party')
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        party = get_object_or_404(Party, id=party_id)
        
        # Check if score already exists for this user and party
        existing_score = GameScore.objects.filter(
            user=request.user, 
            party=party
        ).first()
        
        if existing_score:
            return Response(
                {'error': 'Score already exists for this user and party'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        score = GameScore.objects.create(
            user=request.user,
            party=party,
            total_points=request.data.get('total_points', 0)
        )
        
        # Update level based on points
        score.level = score.calculate_level()
        score.save()
        
        serializer = self.get_serializer(score)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        score = self.get_object()
        
        # Check if user owns this score or is the party host
        if score.user != request.user and score.party.host != request.user:
            return Response(
                {'error': 'You can only update your own scores or scores for your parties'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle points_to_add
        points_to_add = request.data.get('points_to_add')
        if points_to_add is not None:
            score.total_points += points_to_add
            score.level = score.calculate_level()
            score.save()
            
            # Check for new badges
            self._check_and_award_badges(score)
            
            serializer = self.get_serializer(score)
            return Response(serializer.data)
        
        return super().update(request, *args, **kwargs)
    
    def _check_and_award_badges(self, score):
        """Check if user has earned any new badges"""
        available_badges = Badge.objects.filter(
            is_active=True,
            points_required__lte=score.total_points
        )
        
        for badge in available_badges:
            UserBadge.objects.get_or_create(
                user=score.user,
                badge=badge,
                party=score.party
            )
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        party_id = request.query_params.get('party_id')
        if not party_id:
            return Response(
                {'error': 'party_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        party = get_object_or_404(Party, id=party_id)
        
        # Get top scores for the party
        limit = int(request.query_params.get('limit', 10))
        scores = GameScore.objects.filter(party=party).select_related('user').order_by('-total_points')[:limit]
        
        leaderboard_data = []
        for rank, score in enumerate(scores, 1):
            badge_count = UserBadge.objects.filter(
                user=score.user, 
                party=party
            ).count()
            
            leaderboard_data.append({
                'rank': rank,
                'user': UserSerializer(score.user).data,
                'total_points': score.total_points,
                'level': score.level,
                'badge_count': badge_count
            })
        
        return Response({
            'party': {
                'id': party.id,
                'name': party.name
            },
            'leaderboard': leaderboard_data
        })
    
    @action(detail=True, methods=['post'])
    def add_points(self, request, pk=None):
        score = self.get_object()
        
        # Check if user is the party host
        if score.party.host != request.user:
            return Response(
                {'error': 'Only the party host can add points'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        points = request.data.get('points', 0)
        if points <= 0:
            return Response(
                {'error': 'Points must be positive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        score.total_points += points
        score.level = score.calculate_level()
        score.save()
        
        # Check for new badges
        self._check_and_award_badges(score)
        
        serializer = self.get_serializer(score)
        return Response(serializer.data)

class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def user_badges(self, request):
        party_id = request.query_params.get('party_id')
        user_id = request.query_params.get('user_id', request.user.id)
        
        badges_query = UserBadge.objects.filter(user_id=user_id).select_related('badge', 'party')
        
        if party_id:
            badges_query = badges_query.filter(party_id=party_id)
        
        serializer = UserBadgeSerializer(badges_query, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_badges(self, request):
        party_id = request.query_params.get('party_id')
        
        if not party_id:
            return Response(
                {'error': 'party_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user's current points for this party
        try:
            score = GameScore.objects.get(user=request.user, party_id=party_id)
            user_points = score.total_points
        except GameScore.DoesNotExist:
            user_points = 0
        
        # Get all badges and mark which ones are earned/available
        badges = Badge.objects.filter(is_active=True)
        earned_badges = UserBadge.objects.filter(
            user=request.user, 
            party_id=party_id
        ).values_list('badge_id', flat=True)
        
        badge_data = []
        for badge in badges:
            badge_info = BadgeSerializer(badge).data
            badge_info['is_earned'] = badge.id in earned_badges
            badge_info['is_available'] = user_points >= badge.points_required
            badge_data.append(badge_info)
        
        return Response(badge_data)
