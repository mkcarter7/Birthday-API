from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from ..models import VenmoPayment, Party
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class VenmoPaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    party_name = serializers.CharField(source='party.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = VenmoPayment
        fields = [
            'id', 'party', 'user', 'amount', 'venmo_transaction_id', 'status',
            'status_display', 'note', 'created_at', 'updated_at', 'party_name',
            'can_edit'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user or obj.party.host == request.user
        return False

class VenmoPaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenmoPayment
        fields = ['amount', 'note']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        if value > 10000:  # Reasonable upper limit
            raise serializers.ValidationError("Amount cannot exceed $10,000.")
        return value

class VenmoPaymentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenmoPayment
        fields = ['status', 'venmo_transaction_id', 'note']

class PaymentSummarySerializer(serializers.Serializer):
    total_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    completed_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    failed_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()

class VenmoPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = VenmoPaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = VenmoPayment.objects.all()
        
        # Users can only see their own payments or payments for parties they host
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(user=self.request.user) | Q(party__host=self.request.user)
            )
        
        # Filter by party if specified
        party_id = self.request.query_params.get('party')
        if party_id:
            queryset = queryset.filter(party_id=party_id)
        
        # Filter by status
        payment_status = self.request.query_params.get('status')
        if payment_status:
            queryset = queryset.filter(status=payment_status)
        
        # Filter by user's payments
        my_payments = self.request.query_params.get('my_payments')
        if my_payments and my_payments.lower() == 'true':
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.select_related('user', 'party')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VenmoPaymentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VenmoPaymentUpdateSerializer
        return VenmoPaymentSerializer
    
    def create(self, request, *args, **kwargs):
        party_id = request.data.get
