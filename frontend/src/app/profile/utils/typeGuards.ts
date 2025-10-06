/**
 * 型ガード関数
 * TypeScriptエラーを解消するための型判定ユーティリティ
 */

import type { ContributorProfile, ProposerProfile } from '../../../types/auth';

/**
 * プロフィールオブジェクトの型定義
 * APIから返されるプロフィールデータの実際の構造に合わせた型
 */
export interface ProfileData {
  contributor_profile?: ContributorProfile;
  proposer_profile?: ProposerProfile;
}

/**
 * Contributor Profileかどうかを判定
 */
export function isContributorProfileData(
  profile: ContributorProfile | ProposerProfile | ProfileData | null
): profile is ProfileData & { contributor_profile: ContributorProfile } {
  return profile !== null && 'contributor_profile' in profile;
}

/**
 * Proposer Profileかどうかを判定
 */
export function isProposerProfileData(
  profile: ContributorProfile | ProposerProfile | ProfileData | null
): profile is ProfileData & { proposer_profile: ProposerProfile } {
  return profile !== null && 'proposer_profile' in profile;
}

/**
 * プロフィールデータからContributorProfileを安全に取得
 */
export function getContributorProfile(
  profile: ContributorProfile | ProposerProfile | ProfileData | null
): ContributorProfile | null {
  if (!profile) return null;
  if (isContributorProfileData(profile)) {
    return profile.contributor_profile;
  }
  return null;
}

/**
 * プロフィールデータからProposerProfileを安全に取得
 */
export function getProposerProfile(
  profile: ContributorProfile | ProposerProfile | ProfileData | null
): ProposerProfile | null {
  if (!profile) return null;
  if (isProposerProfileData(profile)) {
    return profile.proposer_profile;
  }
  return null;
}
