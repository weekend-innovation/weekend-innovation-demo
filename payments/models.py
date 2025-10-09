"""
報酬・ウォレット管理モデル
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
from django.core.validators import MinValueValidator


class Wallet(models.Model):
    """
    ユーザーのウォレット情報
    投稿者・提案者両方のユーザーが持つ
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name='ユーザー'
    )
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='残高'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='メタデータ'
    )  # Stripeアカウント情報等を保存
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = 'ウォレット'
        verbose_name_plural = 'ウォレット'

    def __str__(self):
        return f"{self.user.username}のウォレット (¥{self.balance})"

    def deposit(self, amount):
        """入金処理"""
        if amount <= 0:
            raise ValueError("入金額は0より大きい必要があります")
        self.balance += amount
        self.save()

    def withdraw(self, amount):
        """出金処理"""
        if amount <= 0:
            raise ValueError("出金額は0より大きい必要があります")
        if self.balance < amount:
            raise ValueError("残高が不足しています")
        self.balance -= amount
        self.save()

    def has_sufficient_balance(self, amount):
        """残高確認"""
        return self.balance >= amount


class Payment(models.Model):
    """
    支払い・受取記録
    """
    PAYMENT_TYPES = [
        ('proposal_reward', '提案報酬'),
        ('adoption_reward', '採用報酬'),
        ('deposit', '入金'),
        ('stripe_deposit', 'Stripe入金'),
        ('withdrawal', '出金'),
    ]

    STATUS_CHOICES = [
        ('pending', '処理中'),
        ('completed', '完了'),
        ('failed', '失敗'),
        ('cancelled', 'キャンセル'),
    ]

    # 支払い者（投稿者）
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments_made',
        verbose_name='支払い者'
    )
    
    # 受取者（提案者）
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments_received',
        verbose_name='受取者'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='金額'
    )
    
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
        verbose_name='支払い種別'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='ステータス'
    )
    
    # 関連する課題・提案
    challenge = models.ForeignKey(
        'challenges.Challenge',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='関連課題'
    )
    
    proposal = models.ForeignKey(
        'proposals.Proposal',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='関連提案'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='説明'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='メタデータ'
    )  # Stripe PaymentIntent ID等を保存
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = '支払い記録'
        verbose_name_plural = '支払い記録'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payer.username} → {self.recipient.username}: ¥{self.amount} ({self.get_payment_type_display()})"

    def process_payment(self):
        """支払い処理を実行"""
        try:
            # 支払い者のウォレットを取得（なければ作成）
            payer_wallet, _ = Wallet.objects.get_or_create(user=self.payer)
            
            # 受取者のウォレットを取得（なければ作成）
            recipient_wallet, _ = Wallet.objects.get_or_create(user=self.recipient)
            
            # 残高確認
            if not payer_wallet.has_sufficient_balance(self.amount):
                self.status = 'failed'
                self.save()
                raise ValueError("支払い者の残高が不足しています")
            
            # 支払い処理
            payer_wallet.withdraw(self.amount)
            recipient_wallet.deposit(self.amount)
            
            # ステータス更新
            self.status = 'completed'
            self.save()
            
            return True
            
        except Exception as e:
            self.status = 'failed'
            self.save()
            raise e

    def cancel_payment(self):
        """支払いをキャンセル"""
        if self.status == 'completed':
            raise ValueError("完了済みの支払いはキャンセルできません")
        
        self.status = 'cancelled'
        self.save()


class PaymentHistory(models.Model):
    """
    支払い履歴（詳細ログ）
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='支払い'
    )
    
    action = models.CharField(
        max_length=50,
        verbose_name='アクション'
    )
    
    details = models.TextField(
        blank=True,
        verbose_name='詳細'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')

    class Meta:
        verbose_name = '支払い履歴'
        verbose_name_plural = '支払い履歴'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payment} - {self.action}"