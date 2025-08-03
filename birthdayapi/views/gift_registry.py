# party_app/views/gift_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import GiftRegistryItem, Party
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class GiftRegistryItemSerializer(serializers.ModelSerializer):
    purchased_by = UserSerializer(read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    can_purchase = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = GiftRegistryItem
        fields = [
            'id', 'party', 'name', 'description', 'price', 'url', 'image',
            'priority', 'priority_display', 'is_purchased', 'purchased_by',
            'purchased_at', 'purchase_note', 'created_at', 'party_name',
            'can_purchase', 'can_edit'
        ]
        read_only_fields = [
            'id', 'is_purchased', 'purchased_by', 'purchased_at', 'created_at'
        ]
    
    def get_can_purchase(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return not obj.is_purchased and obj.party.host != request.user
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.party.host == request.user
        return False

class GiftRegistryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftRegistryItem
        fields = [
            'name', 'description', 'price', 'url', 'image', 'priority'
        ]
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

class GiftRegistryStatsSerializer(serializers.Serializer):
    total_items = serializers.IntegerField()
    purchased_items = serializers.IntegerField()
    available_items = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    purchased_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    available_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    completion_percentage = serializers.FloatField()

class GiftRegistryItemViewSet(viewsets.ModelViewSet):
    serializer_class = GiftRegistryItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = GiftRegistryItem.objects.all()
        
        # Filter by party if specified
        party_id = self.request.query_params.get('party')
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Filter by availability
        available_only = self.request.query_params.get('available_only')
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(is_purchased=False)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset.select_related('party', 'purchased_by')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GiftRegistryCreateUpdateSerializer
        return GiftRegistryItemSerializer
    
    def create(self, request, *args, **kwargs):
        party_id = request.data.get('party')
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        party = get_object_or_404(Party, id=party_id)
        
        # Check if user is the party host
        if party.host != request.user:
            return Response(
                {'error': 'Only the party host can add items to the gift registry'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(party=party)
            
            # Return full item data
            response_serializer = GiftRegistryItemSerializer(
                serializer.instance,
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        item = self.get_object()
        
        # Check if user is the party host
        if item.party.host != request.user:
            return Response(
                {'error': 'Only the party host can edit gift registry items'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        
        # Check if user is the party host
        if item.party.host != request.user:
            return Response(
                {'error': 'Only the party host can delete gift registry items'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        item = self.get_object()
        
        # Check if item is already purchased
        if item.is_purchased:
            return Response(
                {'error': 'This item has already been purchased'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is not the party host
        if item.party.host == request.user:
            return Response(
                {'error': 'Party hosts cannot purchase items from their own registry'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        purchase_note = request.data.get('purchase_note', '')
        
        item.is_purchased = True
        item.purchased_by = request.user
        item.purchased_at = timezone.now()
        item.purchase_note = purchase_note
        item.save()
        
        serializer = self.get_serializer(item)
        return Response({
            'message': 'Item marked as purchased successfully',
            'item': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def unpurchase(self, request, pk=None):
        item = self.get_object()
        
        # Check if user purchased this item or is the party host
        if item.purchased_by != request.user and item.party.host != request.user:
            return Response(
                {'error': 'You can only unpurchase items you purchased or if you are the party host'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        item.is_purchased = False
        item.purchased_by = None
        item.purchased_at = None
        item.purchase_note = ''
        item.save()
        
        serializer = self.get_serializer(item)
        return Response({
            'message': 'Item marked as available successfully',
            'item': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def party_registry(self, request):
        party_id = request.query_params.get('party_id')
        if not party_id:
            return Response(
                {'error': 'party_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        party = get_object_or_404(Party, id=party_id)
        items = GiftRegistryItem.objects.filter(party=party).select_related('purchased_by')
        
        serializer = self.get_serializer(items, many=True)
        return Response({
            'party': {
                'id': party.id,
                'name': party.name,
                'host': party.host.username
            },
            'items': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def registry_stats(self, request):
        party_id = request.query_params.get
