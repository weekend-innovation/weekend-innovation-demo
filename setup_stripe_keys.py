#!/usr/bin/env python3
"""
Stripeキー設定スクリプト
実際のStripeテストキーをsettings.pyに設定します
"""

import os
import sys

def update_stripe_keys():
    """Stripeキーを設定ファイルに更新"""
    
    print("=== Stripeキー設定 ===")
    print("1. https://dashboard.stripe.com/test/apikeys でキーを取得してください")
    print()
    
    # キーを入力
    publishable_key = input("Publishable key (pk_test_...): ").strip()
    secret_key = input("Secret key (sk_test_...): ").strip()
    
    if not publishable_key.startswith('pk_test_') or not secret_key.startswith('sk_test_'):
        print("エラー: 正しいテストキーを入力してください")
        return False
    
    # settings.pyのパス
    settings_path = os.path.join('mvp_project', 'settings.py')
    
    if not os.path.exists(settings_path):
        print(f"エラー: {settings_path} が見つかりません")
        return False
    
    # ファイルを読み込み
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # キーを置換
    content = content.replace(
        "STRIPE_PUBLISHABLE_KEY = 'pk_test_51234567890abcdef'",
        f"STRIPE_PUBLISHABLE_KEY = '{publishable_key}'"
    )
    content = content.replace(
        "STRIPE_SECRET_KEY = 'sk_test_51234567890abcdef'",
        f"STRIPE_SECRET_KEY = '{secret_key}'"
    )
    
    # ファイルに書き込み
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Stripeキーが設定されました")
    print("🔄 サーバーを再起動してください: python manage.py runserver")
    return True

if __name__ == "__main__":
    update_stripe_keys()
