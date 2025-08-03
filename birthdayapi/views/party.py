from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import Party, WeatherData, PartyTimelineEvent
from rest_framework import serializers

from birthdayapi import models

class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = ['temperature', 'condition', 'icon', 'humidity', 'wind_speed', 'updated_at']

class PartyTimelineEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyTimelineEvent
        fields = ['id', 'time', 'activity', 'description', 'icon', 'duration_minutes']

class PartySerializer(serializers.ModelSerializer):
    host = serializers.StringRelatedField(read_only=True)
    weather = WeatherDataSerializer(read_only=True)
    timeline_events = PartyTimelineEventSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()
    is_host = serializers.SerializerMethodField()
    
    class Meta:
        model = Party
        fields = [
            'id', 'name', 'description', 'date', 'end_time', 'location', 'theme',
            'host', 'facebook_live_url', 'venmo_username', 'latitude', 'longitude',
            'is_active', 'is_public', 'max_guests', 'created_at', 'updated_at',
            'weather', 'timeline_events', 'stats', 'is_host'
        ]
        read_only_fields = ['id', 'host', 'created_at', 'updated_at']
    
    def get_stats(self, obj):
        return {
            'total_rsvps': obj.total_rsvps,
            'attending_count': obj.attending_count,
            'photo_count': obj.photos.count(),
            'gift_registry_count': obj.gift_registry.count(),
            'gifts_purchased': obj.gift_registry.filter(is_purchased=True).count(),
        }
    
    def get_is_host(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.host == request.user
        return False

class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Party.objects.all()
        
        # Filter by public parties or user's own parties
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                models.Q(is_public=True) | 
                models.Q(host=self.request.user) |
                models.Q(rsvps__user=self.request.user)
            ).distinct()
        
        # Filter parameters
        theme = self.request.query_params.get('theme')
        is_past = self.request.query_params.get('is_past')
        
        if theme:
            queryset = queryset.filter(theme=theme)
        
        if is_past is not None:
            if is_past.lower() == 'true':
                queryset = queryset.filter(date__lt=timezone.now())
            else:
                queryset = queryset.filter(date__gte=timezone.now())
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(host=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_timeline_event(self, request, pk=None):
        party = self.get_object()
        
        # Check if user is the host
        if party.host != request.user:
            return Response(
                {'error': 'Only the host can add timeline events'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PartyTimelineEventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(party=party)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def weather(self, request, pk=None):
        party = self.get_object()
        weather_data = getattr(party, 'weather', None)
        
        if weather_data:
            serializer = WeatherDataSerializer(weather_data)
            return Response(serializer.data)
        
        return Response(
            {'message': 'No weather data available'},
            status=status.HTTP_404_NOT_FOUND
        )
