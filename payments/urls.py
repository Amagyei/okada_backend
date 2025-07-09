from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentMethodViewSet,
    TransactionViewSet,
    DriverEarningViewSet,
    WalletViewSet,
    WalletTransactionViewSet,
)

router = DefaultRouter()
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-methods')
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(r'driver-earnings', DriverEarningViewSet, basename='driver-earnings')
router.register(r'wallets', WalletViewSet, basename='wallets')
router.register(r'wallet-transactions', WalletTransactionViewSet, basename='wallet-transactions')

urlpatterns = [
    path('', include(router.urls)),
]