from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from ..models import PartyPhoto, PhotoLike, Party
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class PartyPhotoSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    likes_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    party_name = serializers.CharField(source='party.name', read_only=True)
    
    class Meta:
        model = PartyPhoto
        fields = [
            'id', 'party', 'image', 'caption', 'uploaded_at', 'uploaded_by',
            'likes_count', 'is_liked', 'is_featured', 'party_name'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'likes_count']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

class PhotoLikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PhotoLike
        fields = ['id', 'user', 'photo', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class PartyPhotoViewSet(viewsets.ModelViewSet):
    serializer_class = PartyPhotoSerializer
    permission_classes = [IsAuthenticated]  # Default to authenticated
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        # Anyone can view photos
        if self.action in ['list', 'retrieve', 'party_gallery']:
            return [AllowAny()]
        # Only admins can delete photos
        elif self.action in ['destroy']:
            return [IsAdminUser()]
        # Authenticated users can upload and like
        else:
            return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = PartyPhoto.objects.all()
        
        # Filter by party if specified
        party_id = self.request.query_params.get('party')
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Filter by user's photos (only if authenticated)
        my_photos = self.request.query_params.get('my_photos')
        if my_photos and my_photos.lower() == 'true' and self.request.user.is_authenticated:
            queryset = queryset.filter(uploaded_by=self.request.user)
        
        # Filter by featured photos
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        return queryset.select_related('uploaded_by', 'party').prefetch_related('likes')
    
    def perform_create(self, serializer):
        # User is already authenticated due to permission classes
        party_id = self.request.data.get('party')
        if not party_id:
            raise serializers.ValidationError("Party ID is required")
        
        party = get_object_or_404(Party, id=party_id)
        serializer.save(uploaded_by=self.request.user, party=party)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        photo = self.get_object()
        like, created = PhotoLike.objects.get_or_create(
            user=request.user,
            photo=photo
        )
        
        if created:
            return Response(
                {'message': 'Photo liked', 'likes_count': photo.likes_count},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Photo already liked', 'likes_count': photo.likes_count},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['delete'])
    def unlike(self, request, pk=None):
        photo = self.get_object()
        
        try:
            like = PhotoLike.objects.get(user=request.user, photo=photo)
            like.delete()
            return Response(
                {'message': 'Photo unliked', 'likes_count': photo.likes_count},
                status=status.HTTP_200_OK
            )
        except PhotoLike.DoesNotExist:
            return Response(
                {'message': 'Photo was not liked', 'likes_count': photo.likes_count},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        photo = self.get_object()
        
        # Check if user is the party host
        if photo.party.host != request.user:
            return Response(
                {'error': 'Only the party host can feature photos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        photo.is_featured = not photo.is_featured
        photo.save()
        
        return Response({
            'message': f'Photo {"featured" if photo.is_featured else "unfeatured"}',
            'is_featured': photo.is_featured
        })
    
    @action(detail=False, methods=['get'])
    def party_gallery(self, request):
        party_id = request.query_params.get('party_id')
        if not party_id:
            return Response(
                {'error': 'party_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        party = get_object_or_404(Party, id=party_id)
        photos = PartyPhoto.objects.filter(party=party).select_related('uploaded_by')
        
        serializer = self.get_serializer(photos, many=True)
        return Response({
            'party': {
                'id': party.id,
                'name': party.name,
                'date': party.date
            },
            'photos': serializer.data
        })
