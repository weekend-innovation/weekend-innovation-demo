from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ContributorProfile, ProposerProfile

# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """カスタムユーザーモデルの管理画面設定"""
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    # フィールドセットの設定
    fieldsets = BaseUserAdmin.fieldsets + (
        ('カスタム情報', {'fields': ('user_type',)}),
    )
    
    # 新規作成時のフィールドセット
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('カスタム情報', {'fields': ('user_type',)}),
    )

@admin.register(ContributorProfile)
class ContributorProfileAdmin(admin.ModelAdmin):
    """投稿者プロフィールの管理画面設定"""
    list_display = ('user', 'company_name', 'representative_name', 'industry', 'created_at')
    list_filter = ('industry', 'created_at')
    search_fields = ('company_name', 'representative_name', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'company_name', 'representative_name')
        }),
        ('連絡先情報', {
            'fields': ('address', 'phone_number', 'email')
        }),
        ('企業情報', {
            'fields': ('industry', 'employee_count', 'established_year', 'company_url', 'company_logo')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProposerProfile)
class ProposerProfileAdmin(admin.ModelAdmin):
    """提案者プロフィールの管理画面設定"""
    list_display = ('user', 'full_name', 'gender', 'occupation', 'created_at')
    list_filter = ('gender', 'occupation', 'created_at')
    search_fields = ('full_name', 'email', 'expertise')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'full_name', 'gender', 'birth_date')
        }),
        ('連絡先情報', {
            'fields': ('address', 'phone_number', 'email')
        }),
        ('プロフィール情報', {
            'fields': ('occupation', 'expertise', 'bio', 'profile_image')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
