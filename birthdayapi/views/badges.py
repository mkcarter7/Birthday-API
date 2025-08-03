from rest_framework import viewsets, status, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Prefetch
from django.contrib.auth.models import User
from ..models import Badge, UserBadge, Party, GameScore


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for Badge model"""
    earned_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'icon', 'points_required', 
            'color', 'is_active', 'earned_count'
        ]
    
    def get_earned_count(self, obj):
        """Get total number of times this badge has been earned"""
        return obj.userbadge_set.count()


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for UserBadge model"""
    badge_name = serializers.CharField(source='badge.name', read_only=True)
    badge_description = serializers.CharField(source='badge.description', read_only=True)
    badge_icon = serializers.CharField(source='badge.icon', read_only=True)
    badge_color = serializers.CharField(source='badge.color', read_only=True)
    badge_points_required = serializers.IntegerField(source='badge.points_required', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    
    class Meta:
        model = UserBadge
        fields = [
            'id', 'user', 'user_username', 'user_first_name', 'user_last_name',
            'badge', 'badge_name', 'badge_description', 'badge_icon', 
            'badge_color', 'badge_points_required', 'party', 'party_name', 
            'earned_at'
        ]
        read_only_fields = ['earned_at']


class BadgeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing badges
    Only admin users can create/update/delete badges
    All authenticated users can view badges
    """
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get badges with optional filtering"""
        queryset = Badge.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search by name or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Filter by points range
        min_points = self.request.query_params.get('min_points')
        max_points = self.request.query_params.get('max_points')
        if min_points:
            queryset = queryset.filter(points_required__gte=min_points)
        if max_points:
            queryset = queryset.filter(points_required__lte=max_points)
        
        return queryset.order_by('points_required')
    
    def get_permissions(self):
        """
        Only admin users can create, update, or delete badges
        All authenticated users can view badges
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def available_for_user(self, request):
        """Get badges that a user can potentially earn based on their current points"""
        party_id = request.query_params.get('party')
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            party = Party.objects.get(pk=party_id)
            user_score = GameScore.objects.filter(
                user=request.user, 
                party=party
            ).first()
            
            if not user_score:
                # User has no score in this party yet
                user_points = 0
            else:
                user_points = user_score.total_points
            
            # Get badges user can earn (has enough points but hasn't earned yet)
            earned_badge_ids = UserBadge.objects.filter(
                user=request.user,
                party=party
            ).values_list('badge_id', flat=True)
            
            available_badges = Badge.objects.filter(
                is_active=True,
                points_required__lte=user_points
            ).exclude(id__in=earned_badge_ids)
            
            # Get badges user is close to earning (within 50 points)
            upcoming_badges = Badge.objects.filter(
                is_active=True,
                points_required__gt=user_points,
                points_required__lte=user_points + 50
            ).exclude(id__in=earned_badge_ids)
            
            available_serializer = self.get_serializer(available_badges, many=True)
            upcoming_serializer = self.get_serializer(upcoming_badges, many=True)
            
            return Response({
                'user_points': user_points,
                'party': {
                    'id': party.id,
                    'name': party.name
                },
                'available_badges': available_serializer.data,
                'upcoming_badges': upcoming_serializer.data
            })
            
        except Party.DoesNotExist:
            return Response(
                {'error': 'Party not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get users with the most badges"""
        party_id = request.query_params.get('party')
        limit = min(int(request.query_params.get('limit', 20)), 100)
        
        if party_id:
            # Party-specific badge leaderboard
            try:
                party = Party.objects.get(pk=party_id)
                
                leaderboard = UserBadge.objects.filter(party=party).values(
                    'user__id', 'user__username', 'user__first_name', 'user__last_name'
                ).annotate(
                    badge_count=Count('badge', distinct=True)
                ).order_by('-badge_count')[:limit]
                
                return Response({
                    'party': {
                        'id': party.id,
                        'name': party.name
                    },
                    'leaderboard': list(leaderboard),
                    'type': 'party'
                })
                
            except Party.DoesNotExist:
                return Response(
                    {'error': 'Party not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Overall badge leaderboard
            leaderboard = UserBadge.objects.values(
                'user__id', 'user__username', 'user__first_name', 'user__last_name'
            ).annotate(
                badge_count=Count('badge', distinct=True),
                parties_count=Count('party', distinct=True)
            ).order_by('-badge_count')[:limit]
            
            return Response({
                'leaderboard': list(leaderboard),
                'type': 'overall'
            })


class UserBadgeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user badges (badge achievements)
    """
    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter user badges based on permissions and parameters"""
        queryset = UserBadge.objects.select_related('user', 'badge', 'party')
        
        # Regular users can only see their own badges, staff can see all
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by party
        party_id = self.request.query_params.get('party')
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Filter by user (for staff)
        user_id = self.request.query_params.get('user')
        if user_id and self.request.user.is_staff:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by badge
        badge_id = self.request.query_params.get('badge')
        if badge_id:
            queryset = queryset.filter(badge_id=badge_id)
        
        return queryset.order_by('-earned_at')
    
    def perform_create(self, serializer):
        """Automatically set the user if not provided"""
        if not serializer.validated_data.get('user'):
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    def create(self, request, *args, **kwargs):
        """Override create to check if user has enough points"""
        badge_id = request.data.get('badge')
        party_id = request.data.get('party')
        user = request.data.get('user', request.user.id)
        
        # Only staff can award badges to other users
        if user != request.user.id and not request.user.is_staff:
            return Response(
                {'error': 'You can only earn badges for yourself.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            badge = Badge.objects.get(pk=badge_id)
            party = Party.objects.get(pk=party_id)
            target_user = User.objects.get(pk=user)
            
            # Check if badge already earned
            if UserBadge.objects.filter(user=target_user, badge=badge, party=party).exists():
                return Response(
                    {'error': 'Badge already earned by this user in this party.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user has enough points (unless staff is awarding)
            if not request.user.is_staff:
                user_score = GameScore.objects.filter(user=target_user, party=party).first()
                user_points = user_score.total_points if user_score else 0
                
                if user_points < badge.points_required:
                    return Response(
                        {
                            'error': f'Not enough points. Required: {badge.points_required}, Current: {user_points}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return super().create(request, *args, **kwargs)
            
        except (Badge.DoesNotExist, Party.DoesNotExist, User.DoesNotExist) as e:
            return Response(
                {'error': f'Invalid {e.__class__.__name__.replace("DoesNotExist", "").lower()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_badges(self, request):
        """Get current user's badges across all parties or specific party"""
        party_id = request.query_params.get('party')
        
        queryset = UserBadge.objects.filter(user=request.user).select_related('badge', 'party')
        
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Group badges by party
        badges_by_party = {}
        for badge_data in serializer.data:
            party_name = badge_data['party_name']
            if party_name not in badges_by_party:
                badges_by_party[party_name] = []
            badges_by_party[party_name].append(badge_data)
        
        return Response({
            'total_badges': queryset.count(),
            'badges_by_party': badges_by_party,
            'all_badges': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def auto_award(self, request):
        """Automatically award badges based on user's current points"""
        party_id = request.data.get('party')
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            party = Party.objects.get(pk=party_id)
            user_score = GameScore.objects.filter(user=request.user, party=party).first()
            
            if not user_score:
                return Response(
                    {'error': 'No game score found for this user in this party'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get already earned badges
            earned_badge_ids = UserBadge.objects.filter(
                user=request.user,
                party=party
            ).values_list('badge_id', flat=True)
            
            # Find badges user can earn
            available_badges = Badge.objects.filter(
                is_active=True,
                points_required__lte=user_score.total_points
            ).exclude(id__in=earned_badge_ids)
            
            # Award badges
            new_badges = []
            for badge in available_badges:
                user_badge = UserBadge.objects.create(
                    user=request.user,
                    badge=badge,
                    party=party
                )
                new_badges.append(user_badge)
            
            serializer = self.get_serializer(new_badges, many=True)
            
            return Response({
                'message': f'Awarded {len(new_badges)} new badges!',
                'new_badges': serializer.data,
                'user_points': user_score.total_points
            })
            
        except Party.DoesNotExist:
            return Response(
                {'error': 'Party not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def party_achievements(self, request):
        """Get badge achievements for a specific party"""
        party_id = request.query_params.get('party')
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            party = Party.objects.get(pk=party_id)
            
            # Get all badge achievements for this party
            achievements = UserBadge.objects.filter(party=party).select_related('user', 'badge')
            
            # Group by badge
            badges_with_earners = {}
            for achievement in achievements:
                badge_id = achievement.badge.id
                if badge_id not in badges_with_earners:
                    badges_with_earners[badge_id] = {
                        'badge': {
                            'id': achievement.badge.id,
                            'name': achievement.badge.name,
                            'description': achievement.badge.description,
                            'icon': achievement.badge.icon,
                            'color': achievement.badge.color,
                            'points_required': achievement.badge.points_required
                        },
                        'earners': []
                    }
                
                badges_with_earners[badge_id]['earners'].append({
                    'user': {
                        'id': achievement.user.id,
                        'username': achievement.user.username,
                        'first_name': achievement.user.first_name,
                        'last_name': achievement.user.last_name
                    },
                    'earned_at': achievement.earned_at
                })
            
            return Response({
                'party': {
                    'id': party.id,
                    'name': party.name
                },
                'total_achievements': achievements.count(),
                'badges_with_earners': list(badges_with_earners.values())
            })
            
        except Party.DoesNotExist:
            return Response(
                {'error': 'Party not found'},
                status=status.HTTP_404_NOT_FOUND
            )
