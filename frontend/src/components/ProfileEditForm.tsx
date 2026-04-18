'use client';

import { useState, useEffect } from 'react';
import { authAPI } from '@/lib/api';
import { UserDetail } from '@/types/auth';

interface ProfileEditFormProps {
  profile: UserDetail;
  onSave: (updatedProfile: UserDetail) => void;
  onCancel: () => void;
}

type ProfileFormState = Record<string, string | number | undefined>;

const ProfileEditForm: React.FC<ProfileEditFormProps> = ({ profile, onSave, onCancel }) => {
  const [formData, setFormData] = useState<ProfileFormState>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (profile.user_type === 'contributor' && profile.contributor_profile) {
      setFormData(profile.contributor_profile as unknown as ProfileFormState);
    } else if (profile.user_type === 'proposer' && profile.proposer_profile) {
      setFormData(profile.proposer_profile as unknown as ProfileFormState);
    }
  }, [profile]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      if (profile.user_type === 'contributor') {
        await authAPI.updateContributorProfile(formData);
      } else {
        await authAPI.updateProposerProfile(formData);
      }

      // プロフィールを再取得
      const updatedProfile = await authAPI.getProfile();
      onSave(updatedProfile);
    } catch (error: unknown) {
      console.error('プロフィール更新エラー:', error);
      const errObj = error as { response?: { data?: { error?: string } } };
      setError(errObj.response?.data?.error || 'プロフィールの更新に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const countryOptions = [
    { value: 'JP', label: '日本' },
    { value: 'US', label: 'アメリカ' },
    { value: 'CN', label: '中国' },
    { value: 'KR', label: '韓国' },
    { value: 'GB', label: 'イギリス' },
    { value: 'DE', label: 'ドイツ' },
    { value: 'FR', label: 'フランス' },
    { value: 'IT', label: 'イタリア' },
    { value: 'ES', label: 'スペイン' },
    { value: 'CA', label: 'カナダ' },
    { value: 'AU', label: 'オーストラリア' },
    { value: 'BR', label: 'ブラジル' },
    { value: 'IN', label: 'インド' },
    { value: 'RU', label: 'ロシア' },
    { value: 'SG', label: 'シンガポール' },
    { value: 'TH', label: 'タイ' },
    { value: 'MY', label: 'マレーシア' },
    { value: 'ID', label: 'インドネシア' },
    { value: 'PH', label: 'フィリピン' },
    { value: 'VN', label: 'ベトナム' },
    { value: 'TW', label: '台湾' },
    { value: 'HK', label: '香港' },
    { value: 'MX', label: 'メキシコ' },
    { value: 'AR', label: 'アルゼンチン' },
    { value: 'CL', label: 'チリ' },
    { value: 'ZA', label: '南アフリカ' },
    { value: 'EG', label: 'エジプト' },
    { value: 'NG', label: 'ナイジェリア' },
    { value: 'KE', label: 'ケニア' },
    { value: 'MA', label: 'モロッコ' },
    { value: 'TR', label: 'トルコ' },
    { value: 'SA', label: 'サウジアラビア' },
    { value: 'AE', label: 'UAE' },
    { value: 'IL', label: 'イスラエル' },
    { value: 'NO', label: 'ノルウェー' },
    { value: 'SE', label: 'スウェーデン' },
    { value: 'DK', label: 'デンマーク' },
    { value: 'FI', label: 'フィンランド' },
    { value: 'NL', label: 'オランダ' },
    { value: 'BE', label: 'ベルギー' },
    { value: 'CH', label: 'スイス' },
    { value: 'AT', label: 'オーストリア' },
    { value: 'PL', label: 'ポーランド' },
    { value: 'CZ', label: 'チェコ' },
    { value: 'HU', label: 'ハンガリー' },
    { value: 'RO', label: 'ルーマニア' },
    { value: 'BG', label: 'ブルガリア' },
    { value: 'HR', label: 'クロアチア' },
    { value: 'SI', label: 'スロベニア' },
    { value: 'SK', label: 'スロバキア' },
    { value: 'LT', label: 'リトアニア' },
    { value: 'LV', label: 'ラトビア' },
    { value: 'EE', label: 'エストニア' },
    { value: 'IE', label: 'アイルランド' },
    { value: 'PT', label: 'ポルトガル' },
    { value: 'GR', label: 'ギリシャ' },
    { value: 'CY', label: 'キプロス' },
    { value: 'MT', label: 'マルタ' },
  ];

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">編集</h1>
            <button
              onClick={onCancel}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors duration-200 cursor-pointer"
            >
              戻る
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {profile.user_type === 'contributor' ? (
              <>
                <div>
                  <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-1">
                    会社名
                  </label>
                  <input
                    id="company_name"
                    name="company_name"
                    type="text"
                    value={formData.company_name || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
                    氏名
                  </label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    value={formData.full_name || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-1">
                    性別
                  </label>
                  <select
                    id="gender"
                    name="gender"
                    value={formData.gender || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="male">男性</option>
                    <option value="female">女性</option>
                    <option value="other">その他</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="birth_date" className="block text-sm font-medium text-gray-700 mb-1">
                    生年月日
                  </label>
                  <input
                    id="birth_date"
                    name="birth_date"
                    type="date"
                    value={formData.birth_date || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                    所在地
                  </label>
                  <input
                    id="location"
                    name="location"
                    type="text"
                    value={formData.location || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
                    住所
                  </label>
                  <input
                    id="address"
                    name="address"
                    type="text"
                    value={formData.address || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700 mb-1">
                    電話番号
                  </label>
                  <input
                    id="phone_number"
                    name="phone_number"
                    type="tel"
                    value={formData.phone_number || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="occupation" className="block text-sm font-medium text-gray-700 mb-1">
                    職業
                  </label>
                  <input
                    id="occupation"
                    name="occupation"
                    type="text"
                    value={formData.occupation || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
                    氏名
                  </label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    value={formData.full_name || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-1">
                    性別
                  </label>
                  <select
                    id="gender"
                    name="gender"
                    value={formData.gender || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="male">男性</option>
                    <option value="female">女性</option>
                    <option value="other">その他</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="birth_date" className="block text-sm font-medium text-gray-700 mb-1">
                    生年月日
                  </label>
                  <input
                    id="birth_date"
                    name="birth_date"
                    type="date"
                    value={formData.birth_date || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="nationality" className="block text-sm font-medium text-gray-700 mb-1">
                    国籍
                  </label>
                  <select
                    id="nationality"
                    name="nationality"
                    value={formData.nationality || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">選択してください</option>
                    {countryOptions.map((country) => (
                      <option key={country.value} value={country.value}>
                        {country.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
                    住所
                  </label>
                  <input
                    id="address"
                    name="address"
                    type="text"
                    value={formData.address || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700 mb-1">
                    電話番号
                  </label>
                  <input
                    id="phone_number"
                    name="phone_number"
                    type="tel"
                    value={formData.phone_number || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="occupation" className="block text-sm font-medium text-gray-700 mb-1">
                    職業
                  </label>
                  <input
                    id="occupation"
                    name="occupation"
                    type="text"
                    value={formData.occupation || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </>
            )}

            <div className="flex justify-end space-x-4 pt-6">
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors duration-200 cursor-pointer"
              >
                キャンセル
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 cursor-pointer"
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProfileEditForm;
