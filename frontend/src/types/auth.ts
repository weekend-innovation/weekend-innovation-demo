/**
 * 認証関連の型定義
 * Weekend Innovationプロジェクトのユーザー認証システム
 * 
 * Phase 1実装内容:
 * - ユーザータイプ定義（投稿者・提案者）
 * - 基本ユーザー情報インターフェース
 * - 投稿者・提案者プロフィールインターフェース
 * - 認証関連のリクエスト・レスポンス型
 * - API エラーレスポンス型
 */

// ユーザータイプ
export type UserType = 'contributor' | 'proposer';

// 基本ユーザー情報
export interface User {
  id: string;
  username: string;
  email: string;
  user_type: UserType;
  created_at: string;
  updated_at: string;
}

// 投稿者プロフィール
export interface ContributorProfile {
  company_name: string;
  representative_name: string;
  location: string;
  address: string;
  phone_number: string;
  industry?: string;
  employee_count?: number;
  established_year?: number;
  company_url?: string;
  company_logo?: string;
}

// 提案者プロフィール
export interface ProposerProfile {
  full_name: string;
  gender: 'male' | 'female' | 'other';
  birth_date: string;
  nationality: string;
  address: string;
  phone_number: string;
  occupation?: string;
  expertise?: string;
  bio?: string;
  profile_image?: string;
}

// ユーザー詳細情報（プロフィール含む）
export interface UserDetail extends User {
  contributor_profile?: ContributorProfile;
  proposer_profile?: ProposerProfile;
}

// 認証トークン
export interface AuthTokens {
  access: string;
  refresh: string;
}

// 認証レスポンス
export interface AuthResponse {
  message: string;
  user: User;
  tokens: AuthTokens;
}

// ログインリクエスト
export interface LoginRequest {
  email: string;
  password: string;
}

// 新規登録リクエスト
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  user_type: UserType;
  profile: ContributorProfile | ProposerProfile;
}

// プロフィール更新リクエスト
export type ProfileUpdateRequest = Record<string, unknown>;

// API エラーレスポンス
export interface ApiError {
  error: string;
  details?: Record<string, string[]>;
}
