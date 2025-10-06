/**
 * ユーザープロフィールページ
 * ユーザーの基本情報とプロフィールを表示・編集
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '../../contexts/AuthContext';
import { authAPI } from '../../lib/api';
import { createStripeAccount, getStripeAccountStatus } from '../../lib/walletAPI';
import ProfileEditForm from '../../components/profile/ProfileEditForm';
import { ProfileField, ProfileSection } from './components/ProfileField';
import { ContributorProfileDisplay, ProposerProfileDisplay } from './components/ProfileDisplay';
import { ProfileData, isContributorProfileData, isProposerProfileData, getContributorProfile, getProposerProfile } from './utils/typeGuards';
import type { User, ContributorProfile, ProposerProfile } from '../../types/auth';

const ProfilePage: React.FC = () => {
  const { user, isAuthenticated, refreshUser } = useAuth();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stripeAccountStatus, setStripeAccountStatus] = useState<{
    has_account: boolean;
    account_status: string | null;
    account_id?: string;
  } | null>(null);
  const [stripeLoading, setStripeLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  // プロフィール情報の取得
  const fetchProfile = async () => {
    if (!user) return;
    
    try {
      const profileData = await authAPI.getProfile();
      console.log('プロフィールデータ:', profileData);
      console.log('ユーザータイプ:', user.user_type);
      console.log('プロフィールタイプ:', profileData.contributor_profile ? 'contributor' : profileData.proposer_profile ? 'proposer' : 'none');
      console.log('提案者プロフィール:', profileData.proposer_profile);
      setProfile(profileData);
      
      // 全ユーザーでStripeアカウント状態を取得
      try {
        const stripeStatus = await getStripeAccountStatus();
        setStripeAccountStatus(stripeStatus);
      } catch (stripeError) {
        // Stripeエラーは無視（プロフィール表示は継続）
        console.warn('Stripeアカウント状態の取得に失敗:', stripeError);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'プロフィールの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // Stripeアカウント作成
  const handleCreateStripeAccount = async () => {
    setStripeLoading(true);
    try {
      const result = await createStripeAccount();
      if (result.onboarding_url) {
        // Stripeのオンボーディングページにリダイレクト
        window.location.href = result.onboarding_url;
      }
    } catch (err) {
      console.error('Stripeアカウント作成エラー:', err);
      alert('Stripeアカウントの作成に失敗しました');
    } finally {
      setStripeLoading(false);
    }
  };

  // プロフィール保存
  const handleSaveProfile = async (updatedProfile: ContributorProfile | ProposerProfile) => {
    if (!user) return;
    
    console.log('保存するプロフィール:', updatedProfile);
    console.log('ユーザータイプ:', user.user_type);
    
    setSaving(true);
    try {
      if (user.user_type === 'contributor') {
        await authAPI.updateContributorProfile(updatedProfile);
      } else {
        await authAPI.updateProposerProfile(updatedProfile);
      }
      
      // プロフィールデータを正しく更新
      if (user.user_type === 'contributor') {
        setProfile(prev => ({
          ...prev,
          contributor_profile: updatedProfile as ContributorProfile
        }) as ProfileData);
      } else {
        setProfile(prev => ({
          ...prev,
          proposer_profile: updatedProfile as ProposerProfile
        }) as ProfileData);
      }
      
      setIsEditing(false);
      await refreshUser(); // ユーザー情報を更新
      await fetchProfile(); // プロフィールデータを再取得
      alert('プロフィールを更新しました');
    } catch (error) {
      console.error('プロフィール更新エラー:', error);
      alert('プロフィールの更新に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  // 編集キャンセル
  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  useEffect(() => {
    fetchProfile();
  }, [user]);

  // 認証チェック
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-blue-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              認証が必要です
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
      <div className="min-h-screen bg-blue-50 py-8">
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
      <div className="min-h-screen bg-blue-50 py-8">
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
    <div className="min-h-screen bg-white py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
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

        {/* プロフィール情報を縦並びで表示 */}
        <div className="space-y-6">
          {/* 編集モードの場合 */}
          {isEditing && profile && (
            <ProfileEditForm
              user={user}
              profile={user.user_type === 'contributor' ? getContributorProfile(profile)! : getProposerProfile(profile)!}
              onSave={handleSaveProfile}
              onCancel={handleCancelEdit}
            />
          )}
          
          {/* 表示モードの場合 */}
          {!isEditing && (
            <>
              {/* 基本情報 */}
              <ProfileSection title="基本情報">
                <ProfileField label="ユーザー名" value={user.username} />
                <ProfileField label="メールアドレス" value={user.email} />
                <ProfileField 
                  label="ユーザータイプ" 
                  value={user.user_type === 'contributor' ? '投稿者' : '提案者'} 
                />
                <ProfileField 
                  label="登録日" 
                  value={new Date(user.created_at).toLocaleDateString('ja-JP')} 
                />
              </ProfileSection>

              {/* 個人情報 */}
              {user.user_type === 'contributor' && profile && isContributorProfileData(profile) ? (
                <ContributorProfileDisplay profile={profile.contributor_profile} />
              ) : user.user_type === 'proposer' && profile && isProposerProfileData(profile) ? (
                <ProposerProfileDisplay profile={profile.proposer_profile} />
              ) : null}

              {/* 編集ボタン（個人情報欄の下に配置） */}
              <div className="flex justify-end">
                    <ProfileField label="会社名" value={profile.contributor_profile.company_name} />
                    <ProfileField label="代表者名" value={profile.contributor_profile.representative_name} />
                      <div>
                        <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">所在地</label>
                        <p className="text-gray-900 text-center">
                          {profile.contributor_profile.location ? 
                            (profile.contributor_profile.location === 'JP' ? '日本' :
                             profile.contributor_profile.location === 'US' ? 'アメリカ' :
                             profile.contributor_profile.location === 'CN' ? '中国' :
                             profile.contributor_profile.location === 'KR' ? '韓国' :
                             profile.contributor_profile.location === 'GB' ? 'イギリス' :
                             profile.contributor_profile.location === 'DE' ? 'ドイツ' :
                             profile.contributor_profile.location === 'FR' ? 'フランス' :
                             profile.contributor_profile.location === 'IT' ? 'イタリア' :
                             profile.contributor_profile.location === 'ES' ? 'スペイン' :
                             profile.contributor_profile.location === 'CA' ? 'カナダ' :
                             profile.contributor_profile.location === 'AU' ? 'オーストラリア' :
                             profile.contributor_profile.location === 'BR' ? 'ブラジル' :
                             profile.contributor_profile.location === 'IN' ? 'インド' :
                             profile.contributor_profile.location === 'RU' ? 'ロシア' :
                             profile.contributor_profile.location === 'SG' ? 'シンガポール' :
                             profile.contributor_profile.location === 'TH' ? 'タイ' :
                             profile.contributor_profile.location === 'MY' ? 'マレーシア' :
                             profile.contributor_profile.location === 'ID' ? 'インドネシア' :
                             profile.contributor_profile.location === 'PH' ? 'フィリピン' :
                             profile.contributor_profile.location === 'VN' ? 'ベトナム' :
                             profile.contributor_profile.location === 'TW' ? '台湾' :
                             profile.contributor_profile.location === 'HK' ? '香港' :
                             profile.contributor_profile.location === 'MX' ? 'メキシコ' :
                             profile.contributor_profile.location === 'AR' ? 'アルゼンチン' :
                             profile.contributor_profile.location === 'CL' ? 'チリ' :
                             profile.contributor_profile.location === 'ZA' ? '南アフリカ' :
                             profile.contributor_profile.location === 'EG' ? 'エジプト' :
                             profile.contributor_profile.location === 'NG' ? 'ナイジェリア' :
                             profile.contributor_profile.location === 'KE' ? 'ケニア' :
                             profile.contributor_profile.location === 'MA' ? 'モロッコ' :
                             profile.contributor_profile.location === 'TR' ? 'トルコ' :
                             profile.contributor_profile.location === 'SA' ? 'サウジアラビア' :
                             profile.contributor_profile.location === 'AE' ? 'UAE' :
                             profile.contributor_profile.location === 'IL' ? 'イスラエル' :
                             profile.contributor_profile.location === 'NO' ? 'ノルウェー' :
                             profile.contributor_profile.location === 'SE' ? 'スウェーデン' :
                             profile.contributor_profile.location === 'DK' ? 'デンマーク' :
                             profile.contributor_profile.location === 'FI' ? 'フィンランド' :
                             profile.contributor_profile.location === 'NL' ? 'オランダ' :
                             profile.contributor_profile.location === 'BE' ? 'ベルギー' :
                             profile.contributor_profile.location === 'CH' ? 'スイス' :
                             profile.contributor_profile.location === 'AT' ? 'オーストリア' :
                             profile.contributor_profile.location === 'PL' ? 'ポーランド' :
                             profile.contributor_profile.location === 'CZ' ? 'チェコ' :
                             profile.contributor_profile.location === 'HU' ? 'ハンガリー' :
                             profile.contributor_profile.location === 'RO' ? 'ルーマニア' :
                             profile.contributor_profile.location === 'BG' ? 'ブルガリア' :
                             profile.contributor_profile.location === 'HR' ? 'クロアチア' :
                             profile.contributor_profile.location === 'SI' ? 'スロベニア' :
                             profile.contributor_profile.location === 'SK' ? 'スロバキア' :
                             profile.contributor_profile.location === 'LT' ? 'リトアニア' :
                             profile.contributor_profile.location === 'LV' ? 'ラトビア' :
                             profile.contributor_profile.location === 'EE' ? 'エストニア' :
                             profile.contributor_profile.location === 'IE' ? 'アイルランド' :
                             profile.contributor_profile.location === 'PT' ? 'ポルトガル' :
                             profile.contributor_profile.location === 'GR' ? 'ギリシャ' :
                             profile.contributor_profile.location === 'CY' ? 'キプロス' :
                             profile.contributor_profile.location === 'MT' ? 'マルタ' :
                             profile.contributor_profile.location === 'LU' ? 'ルクセンブルク' :
                             profile.contributor_profile.location === 'IS' ? 'アイスランド' :
                             profile.contributor_profile.location === 'LI' ? 'リヒテンシュタイン' :
                             profile.contributor_profile.location === 'MC' ? 'モナコ' :
                             profile.contributor_profile.location === 'SM' ? 'サンマリノ' :
                             profile.contributor_profile.location === 'VA' ? 'バチカン' :
                             profile.contributor_profile.location === 'AD' ? 'アンドラ' :
                             profile.contributor_profile.location === 'NZ' ? 'ニュージーランド' :
                             profile.contributor_profile.location === 'OTHER' ? 'その他' :
                             profile.contributor_profile.location) : '未設定'}
                        </p>
                      </div>
                      <div className="text-center">
                        <label className="block text-sm font-medium text-gray-500 mb-1">業種</label>
                        <p className="text-gray-900">{profile.contributor_profile.industry}</p>
                      </div>
                      <div className="text-center">
                        <label className="block text-sm font-medium text-gray-500 mb-1">住所</label>
                        <p className="text-gray-900">{profile.contributor_profile.address}</p>
                      </div>
                      <div className="text-center">
                        <label className="block text-sm font-medium text-gray-500 mb-1">電話番号</label>
                        <p className="text-gray-900">{profile.contributor_profile.phone_number}</p>
                      </div>
                      <div className="text-center">
                        <label className="block text-sm font-medium text-gray-500 mb-1">従業員数</label>
                        <p className="text-gray-900">{profile.contributor_profile.employee_count || '未設定'}</p>
                      </div>
                      <div className="text-center">
                        <label className="block text-sm font-medium text-gray-500 mb-1">設立年</label>
                        <p className="text-gray-900">{profile.contributor_profile.established_year || '未設定'}</p>
                      </div>
                      {profile.contributor_profile.company_url && (
                        <div className="text-center">
                          <label className="block text-sm font-medium text-gray-500 mb-1">会社URL</label>
                          <a 
                            href={profile.contributor_profile.company_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 text-lg inline-block"
                          >
                            {profile.contributor_profile.company_url}
                          </a>
                        </div>
                      )}
                  </div>
                ) : user.user_type === 'proposer' && profile && profile.proposer_profile ? (
                  <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">氏名</label>
                        <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                          <p className="text-gray-900">{profile.proposer_profile.full_name}</p>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">性別</label>
                        <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                          <p className="text-gray-900">
                            {profile.proposer_profile.gender === 'male' ? '男性' : 
                             profile.proposer_profile.gender === 'female' ? '女性' : 'その他'}
                          </p>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">生年月日</label>
                        <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                          <p className="text-gray-900">{new Date(profile.proposer_profile.birth_date).toLocaleDateString('ja-JP')}</p>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">国籍</label>
                        <p className="text-gray-900 text-center">
                          {profile.proposer_profile.nationality ? 
                            (profile.proposer_profile.nationality === 'JP' ? '日本' :
                             profile.proposer_profile.nationality === 'US' ? 'アメリカ' :
                             profile.proposer_profile.nationality === 'CN' ? '中国' :
                             profile.proposer_profile.nationality === 'KR' ? '韓国' :
                             profile.proposer_profile.nationality === 'GB' ? 'イギリス' :
                             profile.proposer_profile.nationality === 'DE' ? 'ドイツ' :
                             profile.proposer_profile.nationality === 'FR' ? 'フランス' :
                             profile.proposer_profile.nationality === 'IT' ? 'イタリア' :
                             profile.proposer_profile.nationality === 'ES' ? 'スペイン' :
                             profile.proposer_profile.nationality === 'CA' ? 'カナダ' :
                             profile.proposer_profile.nationality === 'AU' ? 'オーストラリア' :
                             profile.proposer_profile.nationality === 'BR' ? 'ブラジル' :
                             profile.proposer_profile.nationality === 'IN' ? 'インド' :
                             profile.proposer_profile.nationality === 'RU' ? 'ロシア' :
                             profile.proposer_profile.nationality === 'SG' ? 'シンガポール' :
                             profile.proposer_profile.nationality === 'TH' ? 'タイ' :
                             profile.proposer_profile.nationality === 'MY' ? 'マレーシア' :
                             profile.proposer_profile.nationality === 'ID' ? 'インドネシア' :
                             profile.proposer_profile.nationality === 'PH' ? 'フィリピン' :
                             profile.proposer_profile.nationality === 'VN' ? 'ベトナム' :
                             profile.proposer_profile.nationality === 'TW' ? '台湾' :
                             profile.proposer_profile.nationality === 'HK' ? '香港' :
                             profile.proposer_profile.nationality === 'MX' ? 'メキシコ' :
                             profile.proposer_profile.nationality === 'AR' ? 'アルゼンチン' :
                             profile.proposer_profile.nationality === 'CL' ? 'チリ' :
                             profile.proposer_profile.nationality === 'ZA' ? '南アフリカ' :
                             profile.proposer_profile.nationality === 'EG' ? 'エジプト' :
                             profile.proposer_profile.nationality === 'NG' ? 'ナイジェリア' :
                             profile.proposer_profile.nationality === 'KE' ? 'ケニア' :
                             profile.proposer_profile.nationality === 'MA' ? 'モロッコ' :
                             profile.proposer_profile.nationality === 'TR' ? 'トルコ' :
                             profile.proposer_profile.nationality === 'SA' ? 'サウジアラビア' :
                             profile.proposer_profile.nationality === 'AE' ? 'UAE' :
                             profile.proposer_profile.nationality === 'IL' ? 'イスラエル' :
                             profile.proposer_profile.nationality === 'NO' ? 'ノルウェー' :
                             profile.proposer_profile.nationality === 'SE' ? 'スウェーデン' :
                             profile.proposer_profile.nationality === 'DK' ? 'デンマーク' :
                             profile.proposer_profile.nationality === 'FI' ? 'フィンランド' :
                             profile.proposer_profile.nationality === 'NL' ? 'オランダ' :
                             profile.proposer_profile.nationality === 'BE' ? 'ベルギー' :
                             profile.proposer_profile.nationality === 'CH' ? 'スイス' :
                             profile.proposer_profile.nationality === 'AT' ? 'オーストリア' :
                             profile.proposer_profile.nationality === 'PL' ? 'ポーランド' :
                             profile.proposer_profile.nationality === 'CZ' ? 'チェコ' :
                             profile.proposer_profile.nationality === 'HU' ? 'ハンガリー' :
                             profile.proposer_profile.nationality === 'RO' ? 'ルーマニア' :
                             profile.proposer_profile.nationality === 'BG' ? 'ブルガリア' :
                             profile.proposer_profile.nationality === 'HR' ? 'クロアチア' :
                             profile.proposer_profile.nationality === 'SI' ? 'スロベニア' :
                             profile.proposer_profile.nationality === 'SK' ? 'スロバキア' :
                             profile.proposer_profile.nationality === 'LT' ? 'リトアニア' :
                             profile.proposer_profile.nationality === 'LV' ? 'ラトビア' :
                             profile.proposer_profile.nationality === 'EE' ? 'エストニア' :
                             profile.proposer_profile.nationality === 'IE' ? 'アイルランド' :
                             profile.proposer_profile.nationality === 'PT' ? 'ポルトガル' :
                             profile.proposer_profile.nationality === 'GR' ? 'ギリシャ' :
                             profile.proposer_profile.nationality === 'CY' ? 'キプロス' :
                             profile.proposer_profile.nationality === 'MT' ? 'マルタ' :
                             profile.proposer_profile.nationality === 'LU' ? 'ルクセンブルク' :
                             profile.proposer_profile.nationality === 'IS' ? 'アイスランド' :
                             profile.proposer_profile.nationality === 'LI' ? 'リヒテンシュタイン' :
                             profile.proposer_profile.nationality === 'MC' ? 'モナコ' :
                             profile.proposer_profile.nationality === 'SM' ? 'サンマリノ' :
                             profile.proposer_profile.nationality === 'VA' ? 'バチカン' :
                             profile.proposer_profile.nationality === 'AD' ? 'アンドラ' :
                             profile.proposer_profile.nationality === 'NZ' ? 'ニュージーランド' :
                             profile.proposer_profile.nationality === 'OTHER' ? 'その他' :
                             profile.proposer_profile.nationality) : '未設定'}
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">住所</label>
                        <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                          <p className="text-gray-900">{profile.proposer_profile.address}</p>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">電話番号</label>
                        <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                          <p className="text-gray-900">{profile.proposer_profile.phone_number}</p>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-500 mb-1 ml-8">職業</label>
                        <div className="bg-blue-50 border border-gray-200 rounded-lg p-3 text-center">
                          <p className="text-gray-900">{profile.proposer_profile.occupation || '未設定'}</p>
                        </div>
                      </div>
                  </div>
                ) : null}
              </div>
              )}
              {/* 旧コード終了 */}

              {/* 編集ボタン（個人情報欄の下に配置） */}
              <div className="flex justify-end">
                <button
                  onClick={() => setIsEditing(true)}
                  disabled={saving}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50"
                >
                  {saving ? '保存中...' : '編集'}
                </button>
              </div>

              {/* 決済アカウント情報（一番下に配置） */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">決済アカウント</h2>
                <div className="space-y-4">
                  {/* ユーザータイプに応じた説明 */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm text-blue-800">
                      {user.user_type === 'contributor' 
                        ? '投稿者：課題への報酬支払い用アカウント'
                        : '提案者：報酬受取・出金用アカウント'
                      }
                    </p>
                  </div>
                  
                  {stripeAccountStatus ? (
                    <>
                      {stripeAccountStatus.has_account ? (
                        <div className="space-y-3">
                          <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${
                              stripeAccountStatus.account_status === 'completed' 
                                ? 'bg-green-500' 
                                : 'bg-yellow-500'
                            }`}></div>
                            <span className="text-sm font-medium">
                              {stripeAccountStatus.account_status === 'completed' 
                                ? '登録完了' 
                                : '登録中'}
                            </span>
                          </div>
                          {stripeAccountStatus.account_status === 'completed' ? (
                            <p className="text-sm text-green-600">
                              {user.user_type === 'contributor' 
                                ? '決済可能な状態です（クレジットカード登録済み）'
                                : '出金可能な状態です（銀行口座登録済み）'
                              }
                            </p>
                          ) : (
                            <p className="text-sm text-yellow-600">
                              登録手続きを完了してください
                            </p>
                          )}
                          {stripeAccountStatus.account_id && (
                            <div className="text-xs text-gray-500">
                              Stripe ID: {`${stripeAccountStatus.account_id.substring(0, 20)}...`}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <p className="text-sm text-gray-600">
                            {user.user_type === 'contributor' 
                              ? 'ウォレット機能を利用するためにStripeアカウントの登録が必要です'
                              : '報酬を受け取るためにStripeアカウントの登録が必要です'
                            }
                          </p>
                          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                            <p className="text-xs text-yellow-800 whitespace-pre-wrap">
                              ⚠️ 実際のStripeテストキーを設定する必要があります。
                              stripe_setup_guide.mdを参照してください。
                            </p>
                          </div>
                          
                          {/* テスト用の説明 */}
                          <div className="bg-blue-50 border border-gray-200 rounded-lg p-3">
                            <p className="text-xs text-gray-700 whitespace-pre-wrap">
                              <strong>テスト環境での動作：</strong>
                              {user.user_type === 'contributor' 
                                ? '• クレジットカード決済でウォレットに入金\n• 課題への報酬支払いが可能'
                                : '• 報酬を自動でウォレットに受取\n• 銀行口座への出金が可能'
                              }
                            </p>
                          </div>
                          <button
                            onClick={handleCreateStripeAccount}
                            disabled={stripeLoading}
                            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {stripeLoading ? '作成中...' : 'Stripeアカウントを作成'}
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-sm text-gray-500">
                      読み込み中...
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

      </div>
    </div>
  );
};

export default ProfilePage;