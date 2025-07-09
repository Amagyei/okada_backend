from django.contrib import admin
from .models import PaymentMethod, Transaction, DriverEarning, Wallet, WalletTransaction

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'provider', 'is_default', 'is_active', 'created_at')
    list_filter = ('method_type', 'provider', 'is_default', 'is_active')
    search_fields = ('user__username',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'ride', 'amount', 'status', 'created_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('transaction_id', 'ride__id')

@admin.register(DriverEarning)
class DriverEarningAdmin(admin.ModelAdmin):
    list_display = ('driver', 'ride', 'amount', 'commission', 'net_amount', 'is_paid', 'created_at')
    list_filter = ('is_paid',)
    search_fields = ('driver__username', 'ride__id')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at', 'updated_at')
    search_fields = ('user__username',)

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'wallet', 'transaction_type', 'amount', 'description', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('wallet__user__username', 'description')