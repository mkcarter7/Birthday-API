from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from ..models import Party
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class PartySerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    total_rsvps = serializers.ReadOnlyField()
    attending_count = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    
    class Meta:
        model = Party
        fields = [
            'id', 'name', 'description', 'date', 'end_time', 'location',
            'host', 'facebook_live_url', 'venmo_username', 'latitude',
            'longitude', 'is_active', 'is_public', 'max_guests',
            'created_at', 'updated_at', 'total_rsvps', 'attending_count', 'is_past'
        ]
        read_only_fields = ['id', 'host', 'created_at', 'updated_at']

class PartyViewSet(viewsets.ModelViewSet):
    serializer_class = PartySerializer
    permission_classes = [AllowAny]  # Default to public access
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Party.objects.all()
        
        # Filter by active parties
        active = self.request.query_params.get('active')
        if active and active.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        
        # Filter by public parties
        public = self.request.query_params.get('public')
        if public and public.lower() == 'true':
            queryset = queryset.filter(is_public=True)
        
        return queryset.select_related('host')
    
    def perform_create(self, serializer):
        serializer.save(host=self.request.user)
    
    @action(detail=True, methods=['get'])
    def rsvps(self, request, pk=None):
        party = self.get_object()
        rsvps = party.rsvps.all()
        # You can add RSVP serialization here if needed
        return Response({'rsvps': []})  # Placeholder
    
    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        party = self.get_object()
        photos = party.photos.all()
        # You can add photo serialization here if needed
        return Response({'photos': []})  # Placeholder