from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import models
from ..models import RSVP, Party
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class RSVPSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = RSVP
        fields = [
            'id', 'party', 'user', 'status', 'status_display', 'guest_count',
            'dietary_restrictions', 'phone_number', 'notes', 'created_at',
            'updated_at', 'party_name'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class RSVPCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSVP
        fields = [
            'status', 'guest_count', 'dietary_restrictions', 'phone_number', 'notes'
        ]
    
    def validate_guest_count(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Guest count must be between 1 and 10.")
        return value

class RSVPSummarySerializer(serializers.Serializer):
    total_rsvps = serializers.IntegerField()
    attending_count = serializers.IntegerField()
    maybe_count = serializers.IntegerField()
    not_attending_count = serializers.IntegerField()
    total_guests = serializers.IntegerField()

class RSVPViewSet(viewsets.ModelViewSet):
    serializer_class = RSVPSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = RSVP.objects.all()
        
        # Filter by party if specified
        party_id = self.request.query_params.get('party')
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Filter by user's RSVPs
        my_rsvps = self.request.query_params.get('my_rsvps')
        if my_rsvps and my_rsvps.lower() == 'true':
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('user', 'party')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RSVPCreateUpdateSerializer
        return RSVPSerializer
    
    def create(self, request, *args, **kwargs):
        party_id = request.data.get('party')
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        party = get_object_or_404(Party, id=party_id)
        
        # Check if RSVP already exists
        existing_rsvp = RSVP.objects.filter(party=party, user=request.user).first()
        if existing_rsvp:
            return Response(
                {'error': 'RSVP already exists for this party'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if party has reached max capacity
        if party.max_guests and party.attending_count >= party.max_guests:
            return Response(
                {'error': 'Party has reached maximum capacity'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, party=party)
            
            # Return full RSVP data
            response_serializer = RSVPSerializer(
                serializer.instance,
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        rsvp = self.get_object()
        
        # Check if user owns this RSVP
        if rsvp.user != request.user:
            return Response(
                {'error': 'You can only update your own RSVP'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        rsvp = self.get_object()
        
        # Check if user owns this RSVP or is the party host
        if rsvp.user != request.user and rsvp.party.host != request.user:
            return Response(
                {'error': 'You can only delete your own RSVP or RSVPs to your parties'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_rsvps(self, request):
        rsvps = RSVP.objects.filter(user=request.user).select_related('party')
        serializer = self.get_serializer(rsvps, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def party_summary(self, request):
        party_id = request.query_params.get('party_id')
        if not party_id:
            return Response(
                {'error': 'party_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        party = get_object_or_404(Party, id=party_id)
        
        # Check if user can view this party's RSVPs
        if not party.is_public and party.host != request.user:
            user_rsvp = RSVP.objects.filter(party=party, user=request.user).exists()
            if not user_rsvp:
                return Response(
                    {'error': 'You do not have permission to view this party\'s RSVPs'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        rsvps = RSVP.objects.filter(party=party)
        
        summary_data = {
            'total_rsvps': rsvps.count(),
            'attending_count': rsvps.filter(status='yes').count(),
            'maybe_count': rsvps.filter(status='maybe').count(),
            'not_attending_count': rsvps.filter(status='no').count(),
            'total_guests': rsvps.filter(status='yes').aggregate(
                total=models.Sum('guest_count')
            )['total'] or 0
        }
        
        serializer = RSVPSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def quick_rsvp(self, request):
        """Quick RSVP with just party ID and status"""
        party_id = request.data.get('party')
        rsvp_status = request.data.get('status', 'yes')
        
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        party = get_object_or_404(Party, id=party_id)
        
        # Update or create RSVP
        rsvp, created = RSVP.objects.update_or_create(
            party=party,
            user=request.user,
            defaults={'status': rsvp_status}
        )
        
        serializer = RSVPSerializer(rsvp, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
