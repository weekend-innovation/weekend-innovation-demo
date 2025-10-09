"""
報酬・ウォレット管理の管理画面設定
"""
from django.contrib import admin
from .models import Wallet, Payment, PaymentHistory


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'payer', 'recipient', 'amount', 'payment_type', 'status', 'created_at']
    list_filter = ['payment_type', 'status', 'created_at']
    search_fields = ['payer__username', 'recipient__username', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('payer', 'recipient', 'amount', 'payment_type', 'status')
        }),
        ('関連情報', {
            'fields': ('challenge', 'proposal', 'description')
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payer', 'recipient', 'challenge', 'proposal')


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['payment', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['payment__payer__username', 'payment__recipient__username', 'details']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment__payer', 'payment__recipient')