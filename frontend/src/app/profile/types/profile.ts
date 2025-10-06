/**
 * プロフィール関連の型定義
 * 型安全性を向上させ、コードの保守性を高める
 */

export interface BasicInfo {
  username: string;
  email: string;
  user_type: 'contributor' | 'proposer';
  created_at: string;
}

export interface ContributorProfile {
  company_name: string;
  representative_name: string;
  location: string;
  industry: string;
  address: string;
  phone_number: string;
  employee_count: string;
}

export interface ProposerProfile {
  full_name: string;
  gender: 'male' | 'female' | 'other';
  birth_date: string;
  nationality: string;
  address: string;
  phone_number: string;
  occupation: string;
}

export interface UserProfile {
  basic_info: BasicInfo;
  personal_info: ContributorProfile | ProposerProfile;
}

/**
 * プロフィール表示用の統一された型
 */
export interface ProfileDisplayData {
  basicInfo: {
    username: string;
    email: string;
    userType: string;
    registrationDate: string;
  };
  personalInfo: {
    fields: Array<{
      label: string;
      value: string;
    }>;
  };
}
