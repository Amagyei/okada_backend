from rest_framework import serializers
from .models import PaymentMethod, Transaction, DriverEarning, Wallet, WalletTransaction
from rides.serializers import RideSerializer

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = (
            'id', 'method_type', 'provider', 'is_default', 'is_active',
            'phone_number', 'card_last_four', 'card_type', 'expiry_month',
            'expiry_year', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = (
            'method_type', 'provider', 'phone_number', 'card_last_four',
            'card_type', 'expiry_month', 'expiry_year'
        )

    def validate(self, data):
        method_type = data.get('method_type')
        if method_type == 'mobile_money' and not data.get('phone_number'):
            raise serializers.ValidationError("Phone number is required for mobile money payment method.")
        if method_type == 'card' and not all([
                data.get('card_last_four'), data.get('card_type'),
                data.get('expiry_month'), data.get('expiry_year')
        ]):
            raise serializers.ValidationError("Card details are required for card payment method.")
        return data

class TransactionSerializer(serializers.ModelSerializer):
    ride = RideSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = (
            'id', 'ride', 'payment_method', 'amount', 'status',
            'transaction_id', 'provider_transaction_id', 'error_message',
            'created_at', 'completed_at'
        )
        read_only_fields = ('id', 'transaction_id', 'created_at', 'completed_at')

class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('ride', 'payment_method', 'amount')

class DriverEarningSerializer(serializers.ModelSerializer):
    ride = RideSerializer(read_only=True)
    
    class Meta:
        model = DriverEarning
        fields = (
            'id', 'ride', 'amount', 'commission', 'net_amount',
            'is_paid', 'paid_at', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'paid_at')

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('id', 'balance', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class WalletTransactionSerializer(serializers.ModelSerializer):
    ride = RideSerializer(read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = ('id', 'transaction_type', 'amount', 'description', 'ride', 'created_at')
        read_only_fields = ('id', 'created_at')

class WalletDepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.PrimaryKeyRelatedField(queryset=PaymentMethod.objects.all())

class WalletWithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.PrimaryKeyRelatedField(queryset=PaymentMethod.objects.all())

    def validate(self, data):
        wallet = self.context.get('wallet')
        if data['amount'] > wallet.balance:
            raise serializers.ValidationError("Insufficient balance in wallet.")
        return data