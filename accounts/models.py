"""
ユーザー認証・プロフィール管理のモデル定義

Weekend Innovationプロジェクトのユーザーシステム
- 投稿者（Contributor）: 企業・個人・行政機関
- 提案者（Proposer）: 個人
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    カスタムユーザーモデル
    投稿者と提案者の2つのユーザータイプを管理
    """
    USER_TYPES = [
        ('contributor', '投稿者'),
        ('proposer', '提案者'),
    ]
    
    # ユーザータイプ（投稿者 or 提案者）
    user_type = models.CharField(
        max_length=20, 
        choices=USER_TYPES,
        verbose_name="ユーザータイプ"
    )
    
    # 作成・更新日時
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class ContributorProfile(models.Model):
    """
    投稿者プロフィールモデル
    企業・個人・行政機関の情報を管理
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='contributor_profile',
        verbose_name="ユーザー"
    )
    
    # 基本情報
    company_name = models.CharField(max_length=100, verbose_name="商号")
    representative_name = models.CharField(max_length=50, verbose_name="代表者名")
    address = models.TextField(verbose_name="住所")
    phone_number = models.CharField(max_length=20, verbose_name="電話番号")
    email = models.EmailField(verbose_name="メールアドレス")
    
    # 企業情報（任意項目）
    industry = models.CharField(max_length=50, verbose_name="業種")
    employee_count = models.IntegerField(null=True, blank=True, verbose_name="従業員数")
    established_year = models.IntegerField(null=True, blank=True, verbose_name="設立年")
    company_url = models.URLField(null=True, blank=True, verbose_name="会社URL")
    company_logo = models.ImageField(
        upload_to='company_logos/', 
        null=True, 
        blank=True, 
        verbose_name="会社ロゴ"
    )
    
    # 作成・更新日時
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        verbose_name = "投稿者プロフィール"
        verbose_name_plural = "投稿者プロフィール"
    
    def __str__(self):
        return f"{self.company_name} ({self.user.username})"


class ProposerProfile(models.Model):
    """
    提案者プロフィールモデル
    個人の情報を管理
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='proposer_profile',
        verbose_name="ユーザー"
    )
    
    # 基本情報
    full_name = models.CharField(max_length=50, verbose_name="氏名")
    gender = models.CharField(
        max_length=10, 
        choices=[
            ('male', '男性'), 
            ('female', '女性'), 
            ('other', 'その他')
        ], 
        verbose_name="性別"
    )
    birth_date = models.DateField(verbose_name="生年月日")
    address = models.TextField(verbose_name="住所")
    phone_number = models.CharField(max_length=20, verbose_name="電話番号")
    email = models.EmailField(verbose_name="メールアドレス")
    
    # 職業・専門分野（任意項目）
    occupation = models.CharField(max_length=50, null=True, blank=True, verbose_name="職業")
    expertise = models.CharField(max_length=100, null=True, blank=True, verbose_name="専門分野")
    bio = models.TextField(null=True, blank=True, verbose_name="自己紹介")
    profile_image = models.ImageField(
        upload_to='profile_images/', 
        null=True, 
        blank=True, 
        verbose_name="プロフィール画像"
    )
    
    # 作成・更新日時
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        verbose_name = "提案者プロフィール"
        verbose_name_plural = "提案者プロフィール"
    
    def __str__(self):
        return f"{self.full_name} ({self.user.username})"