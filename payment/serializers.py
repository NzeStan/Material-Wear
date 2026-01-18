# payment/serializers.py
from rest_framework import serializers
from .models import PaymentTransaction
from order.serializers import BaseOrderSerializer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import PaymentTransaction


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for payment transactions"""
    orders = BaseOrderSerializer(many=True, read_only=True)
    order_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'reference', 'amount', 'email', 'status', 
            'created', 'modified', 'orders', 'order_count'  # ✅ FIXED: updated → modified
        ]
        read_only_fields = ['id', 'reference', 'created', 'modified']  # ✅ FIXED: updated → modified
    
    def get_order_count(self, obj: 'PaymentTransaction') -> int:
        """Get count of orders in this payment"""
        return obj.orders.count()


class InitiatePaymentSerializer(serializers.Serializer):
    """Serializer for payment initialization"""
    # No input fields needed - uses pending_orders from session
    pass


class PaymentResponseSerializer(serializers.Serializer):
    """Serializer for payment initialization response"""
    authorization_url = serializers.URLField()
    access_code = serializers.CharField()
    reference = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for payment verification"""
    reference = serializers.CharField()


class PaymentStatusSerializer(serializers.Serializer):
    """Serializer for payment status response"""
    reference = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid = serializers.BooleanField()
    message = serializers.CharField()

class WebhookSerializer(serializers.Serializer):
    """Serializer for Paystack webhook endpoint"""
    event = serializers.CharField(help_text="Event type")
    data = serializers.DictField(help_text="Event data")