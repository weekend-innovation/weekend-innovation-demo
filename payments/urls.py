"""
報酬・ウォレット管理のURL設定
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # ウォレット関連
    path('wallet/', views.WalletDetailView.as_view(), name='wallet-detail'),
    path('wallet/balance/', views.wallet_balance, name='wallet-balance'),
    path('wallet/deposit/', views.deposit_money, name='deposit-money'),
    
    # Stripe決済関連
    path('stripe/create-payment-intent/', views.create_payment_intent, name='create-payment-intent'),
    path('stripe/confirm-payment/', views.confirm_payment, name='confirm-payment'),
    
    # Stripeアカウント管理
    path('stripe/create-account/', views.create_stripe_account, name='create-stripe-account'),
    path('stripe/create-customer/', views.create_stripe_customer, name='create-stripe-customer'),
    path('stripe/account-status/', views.get_stripe_account_status, name='stripe-account-status'),
    
    # 出金機能
    path('withdraw/', views.create_withdrawal, name='create-withdrawal'),
    
    # 支払い関連
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment-create'),
    path('payments/<int:payment_id>/process/', views.process_payment, name='process-payment'),
    path('payments/<int:payment_id>/cancel/', views.cancel_payment, name='cancel-payment'),
    
    # 統計
    path('stats/', views.payment_stats, name='payment-stats'),
]
