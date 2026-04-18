/**
 * プロフィール編集フォームコンポーネント
 */
'use client';

import React, { useState } from 'react';
import type { User, ContributorProfile, ProposerProfile } from '../../types/auth';

interface ProfileEditFormProps {
  user: User;
  profile: ContributorProfile | ProposerProfile;
  onSave: (updatedProfile: ContributorProfile | ProposerProfile) => void;
  onCancel: () => void;
}

const ProfileEditForm: React.FC<ProfileEditFormProps> = ({ user, profile, onSave, onCancel }) => {
  const [editedProfile, setEditedProfile] = useState<ContributorProfile | ProposerProfile>(profile);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(editedProfile);
  };

  const handleChange = (field: string, value: string | number) => {
    setEditedProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {user.user_type === 'contributor' ? '企業情報の編集' : '個人情報の編集'}
      </h3>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {user.user_type === 'contributor' && 'company_name' in editedProfile ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">会社名</label>
                <input
                  type="text"
                  value={editedProfile.company_name}
                  onChange={(e) => handleChange('company_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">代表者名</label>
                <input
                  type="text"
                  value={editedProfile.full_name}
                  onChange={(e) => handleChange('full_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">住所</label>
              <input
                type="text"
                value={editedProfile.address}
                onChange={(e) => handleChange('address', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">電話番号</label>
              <input
                type="tel"
                value={editedProfile.phone_number}
                onChange={(e) => handleChange('phone_number', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">業種</label>
                <input
                  type="text"
                  value={editedProfile.industry}
                  onChange={(e) => handleChange('industry', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">従業員数</label>
                <input
                  type="number"
                  value={editedProfile.employee_count || ''}
                  onChange={(e) => handleChange('employee_count', parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">設立年</label>
              <input
                type="number"
                value={editedProfile.established_year || ''}
                onChange={(e) => handleChange('established_year', parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="例: 2020"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">所在地</label>
              <select
                value={editedProfile.location || ''}
                onChange={(e) => handleChange('location', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">選択してください</option>
                <option value="JP">日本</option>
                <option value="US">アメリカ</option>
                <option value="CN">中国</option>
                <option value="KR">韓国</option>
                <option value="GB">イギリス</option>
                <option value="DE">ドイツ</option>
                <option value="FR">フランス</option>
                <option value="IT">イタリア</option>
                <option value="ES">スペイン</option>
                <option value="CA">カナダ</option>
                <option value="AU">オーストラリア</option>
                <option value="BR">ブラジル</option>
                <option value="IN">インド</option>
                <option value="RU">ロシア</option>
                <option value="SG">シンガポール</option>
                <option value="TH">タイ</option>
                <option value="MY">マレーシア</option>
                <option value="ID">インドネシア</option>
                <option value="PH">フィリピン</option>
                <option value="VN">ベトナム</option>
                <option value="TW">台湾</option>
                <option value="HK">香港</option>
                <option value="MX">メキシコ</option>
                <option value="AR">アルゼンチン</option>
                <option value="CL">チリ</option>
                <option value="ZA">南アフリカ</option>
                <option value="EG">エジプト</option>
                <option value="NG">ナイジェリア</option>
                <option value="KE">ケニア</option>
                <option value="MA">モロッコ</option>
                <option value="TR">トルコ</option>
                <option value="SA">サウジアラビア</option>
                <option value="AE">UAE</option>
                <option value="IL">イスラエル</option>
                <option value="NO">ノルウェー</option>
                <option value="SE">スウェーデン</option>
                <option value="DK">デンマーク</option>
                <option value="FI">フィンランド</option>
                <option value="NL">オランダ</option>
                <option value="BE">ベルギー</option>
                <option value="CH">スイス</option>
                <option value="AT">オーストリア</option>
                <option value="PL">ポーランド</option>
                <option value="CZ">チェコ</option>
                <option value="HU">ハンガリー</option>
                <option value="RO">ルーマニア</option>
                <option value="BG">ブルガリア</option>
                <option value="HR">クロアチア</option>
                <option value="SI">スロベニア</option>
                <option value="SK">スロバキア</option>
                <option value="LT">リトアニア</option>
                <option value="LV">ラトビア</option>
                <option value="EE">エストニア</option>
                <option value="IE">アイルランド</option>
                <option value="PT">ポルトガル</option>
                <option value="GR">ギリシャ</option>
                <option value="CY">キプロス</option>
                <option value="MT">マルタ</option>
                <option value="LU">ルクセンブルク</option>
                <option value="IS">アイスランド</option>
                <option value="LI">リヒテンシュタイン</option>
                <option value="MC">モナコ</option>
                <option value="SM">サンマリノ</option>
                <option value="VA">バチカン</option>
                <option value="AD">アンドラ</option>
                <option value="NZ">ニュージーランド</option>
                <option value="OTHER">その他</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">会社URL</label>
              <input
                type="url"
                value={editedProfile.company_url || ''}
                onChange={(e) => handleChange('company_url', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </>
        ) : user.user_type === 'proposer' && 'nationality' in editedProfile ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">氏名</label>
                <input
                  type="text"
                  value={editedProfile.full_name}
                  onChange={(e) => handleChange('full_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">性別</label>
                <select
                  value={editedProfile.gender}
                  onChange={(e) => handleChange('gender', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="male">男性</option>
                  <option value="female">女性</option>
                  <option value="other">その他</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">生年月日</label>
              <input
                type="date"
                value={editedProfile.birth_date}
                onChange={(e) => handleChange('birth_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">住所</label>
              <input
                type="text"
                value={editedProfile.address}
                onChange={(e) => handleChange('address', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">電話番号</label>
              <input
                type="tel"
                value={editedProfile.phone_number}
                onChange={(e) => handleChange('phone_number', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">国籍</label>
              <select
                value={editedProfile.nationality || ''}
                onChange={(e) => handleChange('nationality', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">選択してください</option>
                <option value="JP">日本</option>
                <option value="US">アメリカ</option>
                <option value="CN">中国</option>
                <option value="KR">韓国</option>
                <option value="GB">イギリス</option>
                <option value="DE">ドイツ</option>
                <option value="FR">フランス</option>
                <option value="IT">イタリア</option>
                <option value="ES">スペイン</option>
                <option value="CA">カナダ</option>
                <option value="AU">オーストラリア</option>
                <option value="BR">ブラジル</option>
                <option value="IN">インド</option>
                <option value="RU">ロシア</option>
                <option value="SG">シンガポール</option>
                <option value="TH">タイ</option>
                <option value="MY">マレーシア</option>
                <option value="ID">インドネシア</option>
                <option value="PH">フィリピン</option>
                <option value="VN">ベトナム</option>
                <option value="TW">台湾</option>
                <option value="HK">香港</option>
                <option value="MX">メキシコ</option>
                <option value="AR">アルゼンチン</option>
                <option value="CL">チリ</option>
                <option value="ZA">南アフリカ</option>
                <option value="EG">エジプト</option>
                <option value="NG">ナイジェリア</option>
                <option value="KE">ケニア</option>
                <option value="MA">モロッコ</option>
                <option value="TR">トルコ</option>
                <option value="SA">サウジアラビア</option>
                <option value="AE">UAE</option>
                <option value="IL">イスラエル</option>
                <option value="NO">ノルウェー</option>
                <option value="SE">スウェーデン</option>
                <option value="DK">デンマーク</option>
                <option value="FI">フィンランド</option>
                <option value="NL">オランダ</option>
                <option value="BE">ベルギー</option>
                <option value="CH">スイス</option>
                <option value="AT">オーストリア</option>
                <option value="PL">ポーランド</option>
                <option value="CZ">チェコ</option>
                <option value="HU">ハンガリー</option>
                <option value="RO">ルーマニア</option>
                <option value="BG">ブルガリア</option>
                <option value="HR">クロアチア</option>
                <option value="SI">スロベニア</option>
                <option value="SK">スロバキア</option>
                <option value="LT">リトアニア</option>
                <option value="LV">ラトビア</option>
                <option value="EE">エストニア</option>
                <option value="IE">アイルランド</option>
                <option value="PT">ポルトガル</option>
                <option value="GR">ギリシャ</option>
                <option value="CY">キプロス</option>
                <option value="MT">マルタ</option>
                <option value="LU">ルクセンブルク</option>
                <option value="IS">アイスランド</option>
                <option value="LI">リヒテンシュタイン</option>
                <option value="MC">モナコ</option>
                <option value="SM">サンマリノ</option>
                <option value="VA">バチカン</option>
                <option value="AD">アンドラ</option>
                <option value="NZ">ニュージーランド</option>
                <option value="OTHER">その他</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">住所</label>
              <input
                type="text"
                value={editedProfile.address}
                onChange={(e) => handleChange('address', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">職業</label>
              <input
                type="text"
                value={editedProfile.occupation || ''}
                onChange={(e) => handleChange('occupation', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
          </>
        ) : null}
        
        <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors duration-200"
          >
            キャンセル
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
          >
            保存
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProfileEditForm;
