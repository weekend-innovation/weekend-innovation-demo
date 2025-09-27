/**
 * ユーザープロフィールページ
 * ユーザーの基本情報とプロフィールを表示・編集
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '../../contexts/AuthContext';
import { authAPI } from '../../lib/api';
import type { User, ContributorProfile, ProposerProfile } from '../../types/auth';

const ProfilePage: React.FC = () => {
  const { user, isAuthenticated, refreshUser } = useAuth();
  const [profile, setProfile] = useState<ContributorProfile | ProposerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // プロフィール情報の取得
  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const profileData = await authAPI.getProfile();
      setProfile(profileData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'プロフィールの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchProfile();
    }
  }, [isAuthenticated]);

  // 認証チェック
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              ログインが必要です
            </h2>
            <p className="text-yellow-700 mb-4">
              プロフィールを表示するにはログインしてください。
            </p>
            <Link
              href="/auth/login"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              ログイン
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ローディング表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-600">読み込み中...</div>
          </div>
        </div>
      </div>
    );
  }

  // エラー表示
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-red-800 mb-2">
              エラーが発生しました
            </h2>
            <p className="text-red-700 mb-4">{error}</p>
            <button
              onClick={fetchProfile}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors duration-200"
            >
              再試行
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!user || !profile) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Link
              href="/dashboard"
              className="text-gray-600 hover:text-gray-800 transition-colors duration-200"
            >
              ← ダッシュボードに戻る
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">プロフィール</h1>
          <p className="mt-2 text-gray-600">
            あなたの基本情報とプロフィールを確認・編集できます
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 基本情報 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">基本情報</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-500">ユーザー名</label>
                  <p className="text-gray-900">{user.username}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">メールアドレス</label>
                  <p className="text-gray-900">{user.email}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">ユーザータイプ</label>
                  <p className="text-gray-900">
                    {user.user_type === 'contributor' ? '投稿者' : '提案者'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">登録日</label>
                  <p className="text-gray-900">
                    {new Date(user.created_at).toLocaleDateString('ja-JP')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* プロフィール詳細 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                {user.user_type === 'contributor' ? '企業情報' : '個人情報'}
              </h2>
              
              {user.user_type === 'contributor' && 'company_name' in profile ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500">会社名</label>
                      <p className="text-gray-900">{profile.company_name}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">代表者名</label>
                      <p className="text-gray-900">{profile.representative_name}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">住所</label>
                    <p className="text-gray-900">{profile.address}</p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500">電話番号</label>
                      <p className="text-gray-900">{profile.phone_number}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">メールアドレス</label>
                      <p className="text-gray-900">{profile.email}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500">業種</label>
                      <p className="text-gray-900">{profile.industry}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">従業員数</label>
                      <p className="text-gray-900">{profile.employee_count || '未設定'}</p>
                    </div>
                  </div>
                  {profile.company_url && (
                    <div>
                      <label className="block text-sm font-medium text-gray-500">会社URL</label>
                      <a 
                        href={profile.company_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                      >
                        {profile.company_url}
                      </a>
                    </div>
                  )}
                </div>
              ) : user.user_type === 'proposer' && 'full_name' in profile ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500">氏名</label>
                      <p className="text-gray-900">{profile.full_name}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">性別</label>
                      <p className="text-gray-900">
                        {profile.gender === 'male' ? '男性' : 
                         profile.gender === 'female' ? '女性' : 'その他'}
                      </p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">住所</label>
                    <p className="text-gray-900">{profile.address}</p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500">電話番号</label>
                      <p className="text-gray-900">{profile.phone_number}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">メールアドレス</label>
                      <p className="text-gray-900">{profile.email}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500">職業</label>
                      <p className="text-gray-900">{profile.occupation || '未設定'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">専門分野</label>
                      <p className="text-gray-900">{profile.expertise || '未設定'}</p>
                    </div>
                  </div>
                  {profile.bio && (
                    <div>
                      <label className="block text-sm font-medium text-gray-500">自己紹介</label>
                      <p className="text-gray-900 whitespace-pre-wrap">{profile.bio}</p>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </div>

        {/* アクションボタン */}
        <div className="mt-8 flex justify-end">
          <button
            onClick={() => {
              // TODO: プロフィール編集機能を実装
              alert('プロフィール編集機能は今後実装予定です');
            }}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
          >
            プロフィールを編集
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
