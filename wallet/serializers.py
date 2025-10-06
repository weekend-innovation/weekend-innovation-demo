"""
報酬・ウォレット管理のシリアライザー
"""
from rest_framework import serializers
from django.conf import settings
from .models import Wallet, Payment, PaymentHistory
from accounts.serializers import UserSerializer


class WalletSerializer(serializers.ModelSerializer):
    """ウォレット情報のシリアライザー"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PaymentHistorySerializer(serializers.ModelSerializer):
    """支払い履歴のシリアライザー"""
    
    class Meta:
        model = PaymentHistory
        fields = ['id', 'action', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    """支払い記録のシリアライザー"""
    payer = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    history = PaymentHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payer', 'recipient', 'amount', 'payment_type', 'status',
            'challenge', 'proposal', 'description', 'history',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'payer', 'created_at', 'updated_at']

    def create(self, validated_data):
        """支払い記録を作成し、自動処理を実行"""
        payment = Payment.objects.create(**validated_data)
        
        # 支払い履歴を記録
        PaymentHistory.objects.create(
            payment=payment,
            action='payment_created',
            details=f'支払い記録が作成されました: {payment.get_payment_type_display()}'
        )
        
        return payment


class CreatePaymentSerializer(serializers.ModelSerializer):
    """支払い作成用のシリアライザー"""
    
    class Meta:
        model = Payment
        fields = [
            'recipient', 'amount', 'payment_type', 'challenge', 'proposal', 'description'
        ]

    def validate_amount(self, value):
        """金額のバリデーション"""
        if value <= 0:
            raise serializers.ValidationError("金額は0より大きい必要があります")
        return value

    def validate(self, data):
        """全体のバリデーション"""
        # 支払い者の残高確認
        payer = self.context['request'].user
        payer_wallet, _ = Wallet.objects.get_or_create(user=payer)
        
        if not payer_wallet.has_sufficient_balance(data['amount']):
            raise serializers.ValidationError("残高が不足しています")
        
        return data


class WalletBalanceSerializer(serializers.Serializer):
    """ウォレット残高情報のシリアライザー"""
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    user_id = serializers.IntegerField()
    username = serializers.CharField()


class PaymentStatsSerializer(serializers.Serializer):
    """支払い統計のシリアライザー"""
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_received = serializers.DecimalField(max_digits=10, decimal_places=2)
    proposal_rewards_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    adoption_rewards_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    proposal_rewards_received = serializers.DecimalField(max_digits=10, decimal_places=2)
    adoption_rewards_received = serializers.DecimalField(max_digits=10, decimal_places=2)
