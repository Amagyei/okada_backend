from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction
from django.utils import timezone
from .models import PaymentMethod, Transaction, DriverEarning, Wallet, WalletTransaction
from .serializers import (
    PaymentMethodSerializer, PaymentMethodCreateSerializer,
    TransactionSerializer, TransactionCreateSerializer,
    DriverEarningSerializer, WalletSerializer,
    WalletTransactionSerializer, WalletDepositSerializer,
    WalletWithdrawalSerializer
)
from .services import process_payment, process_withdrawal

class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentMethodCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        payment_method = self.get_object()
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)
        payment_method.is_default = True
        payment_method.save()
        return Response(self.get_serializer(payment_method).data)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(ride__rider=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        return super().get_serializer_class()

    @db_transaction.atomic
    def perform_create(self, serializer):
        ride = serializer.validated_data['ride']
        payment_method = serializer.validated_data['payment_method']
        amount = serializer.validated_data['amount']

        # Create transaction with a unique transaction_id
        txn = serializer.save(
            transaction_id=f"TXN_{timezone.now().strftime('%Y%m%d%H%M%S')}_{ride.id}"
        )

        # Process payment using our placeholder MTN MoMo integration
        success, result = process_payment(txn)
        
        if success:
            ride.payment_status = 'completed'
            ride.save()
            # Create driver earning if applicable
            if ride.driver:
                DriverEarning.objects.create(
                    driver=ride.driver,
                    ride=ride,
                    amount=amount,
                    commission=amount * 0.2,  # example commission rate
                    net_amount=amount * 0.8
                )
            # Return a custom response (this could also be handled differently)
            raise Exception(f"Payment initiated successfully. Payment URL: {result}")
        else:
            txn.status = "failed"
            txn.error_message = result
            txn.save()
            raise Exception(f"Payment failed: {result}")

class DriverEarningViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DriverEarningSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DriverEarning.objects.filter(driver=self.request.user)

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        wallet = self.get_object()
        serializer = WalletDepositSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            payment_method = serializer.validated_data['payment_method']
            wallet_txn = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='deposit',
                amount=amount,
                description=f'Deposit via {payment_method.get_provider_display()}'
            )
            success, result = process_payment(wallet_txn)
            if success:
                return Response({
                    'message': 'Deposit initiated successfully',
                    'payment_url': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        wallet = self.get_object()
        serializer = WalletWithdrawalSerializer(data=request.data, context={'wallet': wallet})
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            payment_method = serializer.validated_data['payment_method']
            wallet_txn = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='withdrawal',
                amount=amount,
                description=f'Withdrawal to {payment_method.get_provider_display()}'
            )
            success, result = process_withdrawal(wallet_txn)
            if success:
                wallet.balance -= amount
                wallet.save()
                return Response({'message': result}, status=status.HTTP_200_OK)
            else:
                return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WalletTransaction.objects.filter(wallet__user=self.request.user)