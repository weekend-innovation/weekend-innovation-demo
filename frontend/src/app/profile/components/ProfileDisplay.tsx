/**
 * プロフィール表示コンポーネント
 * リファクタリング: 企業情報と個人情報の表示ロジックを統一
 */

import React from 'react';
import { ProfileField, ProfileSection } from './ProfileField';
import type { ContributorProfile, ProposerProfile } from '../../../types/auth';
import { countryCodeToJapanese, genderToJapanese } from '../utils/countryMapping';

interface ContributorDisplayProps {
  profile: ContributorProfile;
}

interface ProposerDisplayProps {
  profile: ProposerProfile;
}

/**
 * 企業情報（Contributor）表示コンポーネント
 */
export const ContributorProfileDisplay: React.FC<ContributorDisplayProps> = ({ profile }) => {
  return (
    <ProfileSection title="企業情報">
      <ProfileField label="会社名" value={profile.company_name} />
      <ProfileField label="代表者名" value={profile.representative_name} />
      <ProfileField 
        label="所在地" 
        value={countryCodeToJapanese(profile.location || '')} 
      />
      <ProfileField label="業種" value={profile.industry} />
      <ProfileField label="住所" value={profile.address} />
      <ProfileField label="電話番号" value={profile.phone_number} />
      <ProfileField label="従業員数" value={profile.employee_count} />
    </ProfileSection>
  );
};

/**
 * 個人情報（Proposer）表示コンポーネント
 */
export const ProposerProfileDisplay: React.FC<ProposerDisplayProps> = ({ profile }) => {
  return (
    <ProfileSection title="個人情報">
      <ProfileField label="氏名" value={profile.full_name} />
      <ProfileField 
        label="性別" 
        value={genderToJapanese(profile.gender)} 
      />
      <ProfileField 
        label="生年月日" 
        value={new Date(profile.birth_date).toLocaleDateString('ja-JP')} 
      />
      <ProfileField 
        label="国籍" 
        value={countryCodeToJapanese(profile.nationality || '')} 
      />
      <ProfileField label="住所" value={profile.address} />
      <ProfileField label="電話番号" value={profile.phone_number} />
      <ProfileField label="職業" value={profile.occupation || '未設定'} />
    </ProfileSection>
  );
};
