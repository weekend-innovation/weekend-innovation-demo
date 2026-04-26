'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI } from '@/lib/api';
import { UserDetail } from '@/types/auth';
import { getNationalityName } from '@/lib/nationalityMapping';
import ProfileEditForm from '@/components/ProfileEditForm';

const ProfilePage = () => {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [profile, setProfile] = useState<UserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);

  // Hooksは常に同じ順序で呼ばれる必要があるため、条件分岐の前に配置
  useEffect(() => {
    if (user && isAuthenticated) {
      fetchProfile();
    }
  }, [user, isAuthenticated]);

  // 認証チェック
  if (authLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-white py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              ログインが必要です
            </h2>
            <p className="text-yellow-700 mb-4">
              プロフィールを閲覧するにはログインが必要です。
            </p>
            <a
              href="/auth/login"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 inline-block"
            >
              ログイン
            </a>
          </div>
        </div>
      </div>
    );
  }

  const fetchProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      setProfile(response);
    } catch (error) {
      console.error('プロフィールの取得に失敗しました:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = (updatedProfile: UserDetail) => {
    setProfile(updatedProfile);
    setIsEditing(false);
    alert('プロフィールを更新しました');
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!user || !profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">プロフィール情報を取得できませんでした</p>
        </div>
      </div>
    );
  }

  if (isEditing) {
    return (
      <ProfileEditForm
        profile={profile}
        onSave={handleSaveProfile}
        onCancel={handleCancelEdit}
      />
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          <h1 className="text-3xl font-bold text-gray-900">プロフィール</h1>

          {/* 基本情報 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">基本情報</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">ユーザー名</label>
                <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                  <p className="text-gray-900">{user.username}</p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">メールアドレス</label>
                <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                  <p className="text-gray-900">{user.email}</p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">ユーザータイプ</label>
                <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                  <p className="text-gray-900">
                    {user.user_type === 'contributor' ? '投稿者' : '提案者'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 詳細情報 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {user.user_type === 'contributor' ? '団体情報' : '個人情報'}
            </h2>
            <div className="space-y-4">
              {user.user_type === 'contributor' ? (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">会社名や自治体名など</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.contributor_profile?.company_name || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">担当者名</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.contributor_profile?.representative_name || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">所在地</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.contributor_profile?.location || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">住所</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.contributor_profile?.address || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">電話番号</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.contributor_profile?.phone_number || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">業種</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.contributor_profile?.industry || '未設定'}</p>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">氏名</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.proposer_profile?.full_name || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">性別</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">
                        {profile.proposer_profile?.gender === 'male' ? '男性' :
                         profile.proposer_profile?.gender === 'female' ? '女性' :
                         profile.proposer_profile?.gender === 'other' ? 'その他' : '未設定'}
                      </p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">生年月日</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.proposer_profile?.birth_date || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">国籍</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.proposer_profile?.nationality ? getNationalityName(profile.proposer_profile.nationality) || '未設定' : '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">住所</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.proposer_profile?.address || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">電話番号</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.proposer_profile?.phone_number || '未設定'}</p>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">職業</label>
                    <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-gray-900">{profile.proposer_profile?.occupation || '未設定'}</p>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 編集ボタン */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={() => setIsEditing(true)}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 cursor-pointer"
            >
              プロフィールを編集
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
