/**
 * 設定ページ
 * ユーザーの設定を管理する画面
 */
'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">設定</h1>
          <p className="mt-2 text-gray-600">
            アカウント設定を管理できます
          </p>
        </div>

        {/* 設定コンテンツ */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="space-y-6">
            {/* ユーザー情報 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">アカウント情報</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">ユーザータイプ</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {user?.user_type === 'contributor' ? '投稿者' : '提案者'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">ユーザー名</label>
                  <p className="mt-1 text-sm text-gray-900">{user?.username}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">メールアドレス</label>
                  <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
                </div>
              </div>
            </div>

            {/* プロフィール設定 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">プロフィール設定</h2>
              <p className="text-sm text-gray-600">
                プロフィールの詳細設定は準備中です。
              </p>
            </div>

            {/* 通知設定 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">通知設定</h2>
              <p className="text-sm text-gray-600">
                通知設定は準備中です。
              </p>
            </div>

            {/* プライバシー設定 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">プライバシー設定</h2>
              <p className="text-sm text-gray-600">
                プライバシー設定は準備中です。
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
