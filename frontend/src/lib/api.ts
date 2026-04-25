/**
 * API呼び出し用のユーティリティ
 * Weekend InnovationプロジェクトのバックエンドAPI連携
 * 
 * Phase 1実装内容:
 * - JWTトークン管理（保存・取得・削除・リフレッシュ）
 * - 認証API呼び出し（ログイン・新規登録・ログアウト）
 * - プロフィール管理API（取得・更新）
 * - 自動トークンリフレッシュ機能
 * - エラーハンドリング・リトライ機能
 * - 認証状態チェック機能
 */

import { 
  AuthResponse, 
  LoginRequest, 
  RegisterRequest, 
  UserDetail, 
  AuthTokens
} from '@/types/auth';

// API ベースURL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// トークン管理
export const tokenManager = {
  // アクセストークンを取得
  getAccessToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  },

  // リフレッシュトークンを取得
  getRefreshToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  },

  // アクセストークンを取得（getTokenのエイリアス）
  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  },

  // トークンを保存
  setTokens: (tokens: AuthTokens): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
  },

  // トークンを削除
  clearTokens: (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  // アクセストークンを更新
  setAccessToken: (access: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', access);
  }
};

// API リクエスト用のヘルパー関数
const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}`;
  const accessToken = tokenManager.getAccessToken();

  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    // 401エラーの場合、トークンをリフレッシュして再試行
    if (response.status === 401 && accessToken) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        config.headers = {
          ...config.headers,
          Authorization: `Bearer ${tokenManager.getAccessToken()}`,
        };
        const retryResponse = await fetch(url, config);
        if (!retryResponse.ok) {
          throw new Error(`HTTP error! status: ${retryResponse.status}`);
        }
        return await retryResponse.json();
      }
    }

    if (!response.ok) {
      // ログアウトAPIの場合は特別な処理
      if (endpoint.includes('/logout/')) {
        console.warn('Logout API returned error status:', response.status);
        return {} as T; // 空のオブジェクトを返す（エラーを無視）
      }
      
      // 401エラーの場合は認証状態をクリア
      if (response.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login';
      }
      
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        console.error('API Error Response:', errorData);
        
        // 空のオブジェクトの場合は特別な処理
        if (Object.keys(errorData).length === 0) {
          errorMessage = `HTTP error! status: ${response.status}`;
        } else {
          errorMessage = errorData.detail || errorData.error || errorData.message || errorMessage;
        }
      } catch (e) {
        // JSON解析に失敗した場合はデフォルトメッセージを使用
        console.error('Failed to parse error response:', e);
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

// アクセストークンのリフレッシュ
const refreshAccessToken = async (): Promise<boolean> => {
  const refreshToken = tokenManager.getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      tokenManager.setAccessToken(data.access);
      return true;
    } else {
      tokenManager.clearTokens();
      return false;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
    tokenManager.clearTokens();
    return false;
  }
};

// 認証関連API
export const authAPI = {
  // ログイン
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiRequest<AuthResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    // トークンを保存
    tokenManager.setTokens(response.tokens);
    
    return response;
  },

  // 新規登録
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiRequest<AuthResponse>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    // トークンを保存
    tokenManager.setTokens(response.tokens);
    
    return response;
  },

  // ログアウト
  logout: async (): Promise<void> => {
    const refreshToken = tokenManager.getRefreshToken();
    const accessToken = tokenManager.getAccessToken();
    
    console.log('Logout attempt - refresh token:', refreshToken ? 'exists' : 'missing');
    console.log('Logout attempt - access token:', accessToken ? 'exists' : 'missing');
    
    if (refreshToken) {
      try {
        // ログアウトAPIを呼び出し（エラーは無視）
        const response = await fetch(`${API_BASE_URL}/auth/logout/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ refresh: refreshToken }),
        });
        
        if (response.ok) {
          console.log('Logout API called successfully');
        } else {
          const errorData = await response.json().catch(() => ({}));
          console.warn('Logout API returned error status:', response.status, errorData);
        }
      } catch (error) {
        // ログアウトAPIのエラーは無視（ローカルログアウトは実行）
        console.warn('Logout API error (ignored):', error);
      }
    } else {
      console.warn('No refresh token found for logout');
    }
    tokenManager.clearTokens();
  },

  // ユーザープロフィール取得
  getProfile: async (): Promise<UserDetail> => {
    return await apiRequest<UserDetail>('/auth/profile/');
  },

  // ユーザー基本情報更新（user.email など）
  updateUserProfile: async (data: Record<string, unknown>): Promise<UserDetail> => {
    return await apiRequest<UserDetail>('/auth/profile/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  // 投稿者プロフィール更新
  updateContributorProfile: async (data: Record<string, unknown>): Promise<UserDetail> => {
    return await apiRequest<UserDetail>('/auth/profile/contributor/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  // 提案者プロフィール更新
  updateProposerProfile: async (data: Record<string, unknown>): Promise<UserDetail> => {
    return await apiRequest<UserDetail>('/auth/profile/proposer/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
};

// 認証状態のチェック
export const isAuthenticated = (): boolean => {
  return !!tokenManager.getAccessToken();
};

// ユーザータイプの取得
export const getUserType = async (): Promise<string | null> => {
  try {
    const profile = await authAPI.getProfile();
    return profile.user_type;
  } catch {
    return null;
  }
};
