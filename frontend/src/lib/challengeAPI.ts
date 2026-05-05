/**
 * 課題関連APIサービス
 */
import { tokenManager } from './api';
import type {
  Challenge,
  ChallengeListItem,
  ChallengeListResponse,
  ChallengeDetailResponse,
  CreateChallengeRequest,
  UpdateChallengeRequest,
  UpdateChallengeStatusRequest,
  ChallengeFilters,
  ChallengeAPIError
} from '../types/challenge';

// API ベースURL
const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/challenges`;

// 共通のAPI呼び出し関数
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = tokenManager.getAccessToken();
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    // 401エラーの場合は認証状態をクリア
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/auth/login';
    }
    
    const errorData: ChallengeAPIError = await response.json().catch(() => ({}));
    
    // エラーメッセージを構築
    let errorMessage = errorData.detail || `HTTP error! status: ${response.status}`;
    
    // フィールド固有のエラーがある場合はそれも含める
    const fieldErrors: string[] = [];
    if (errorData.required_participants && Array.isArray(errorData.required_participants)) {
      fieldErrors.push(...errorData.required_participants);
    }
    if (errorData.title && Array.isArray(errorData.title)) {
      fieldErrors.push(...errorData.title);
    }
    if (errorData.description && Array.isArray(errorData.description)) {
      fieldErrors.push(...errorData.description);
    }
    if (errorData.deadline && Array.isArray(errorData.deadline)) {
      fieldErrors.push(...errorData.deadline);
    }
    if (errorData.adoption_reward && Array.isArray(errorData.adoption_reward)) {
      fieldErrors.push(...errorData.adoption_reward);
    }
    if (errorData.non_field_errors && Array.isArray(errorData.non_field_errors)) {
      fieldErrors.push(...errorData.non_field_errors);
    }
    
    // フィールドエラーがある場合はそれを使用
    if (fieldErrors.length > 0) {
      errorMessage = fieldErrors.join('\n');
    }
    
    throw new Error(errorMessage);
  }
  
  // 削除API（204 No Content）の場合はJSONパースを避ける
  if (response.status === 204) {
    return undefined as T;
  }
  
  return response.json();
}

// 課題一覧取得
export async function getChallenges(
  filters?: ChallengeFilters
): Promise<ChallengeListResponse> {
  const params = new URLSearchParams();
  
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value.toString());
      }
    });
  }
  
  const queryString = params.toString();
  const endpoint = queryString ? `/?${queryString}` : '/';
  
  return apiCall<ChallengeListResponse>(endpoint);
}

/**
 * 課題一覧を全件取得（ページネーションを辿って結合）
 * 投稿者・提案者の一覧表示で20件制限による課題の欠落を防ぐ
 */
export async function getAllChallenges(
  filters?: ChallengeFilters
): Promise<ChallengeListItem[]> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value.toString());
      }
    });
  }
  const queryString = params.toString();

  const token = tokenManager.getAccessToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };

  let allResults: ChallengeListItem[] = [];
  let nextUrl: string | null = `${API_BASE_URL}${queryString ? `/?${queryString}` : '/'}`;

  while (nextUrl) {
    const response = await fetch(nextUrl, { headers });
    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login';
      }
      const err: ChallengeAPIError = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP error! status: ${response.status}`);
    }
    const data: ChallengeListResponse = await response.json();
    if (data.results && data.results.length > 0) {
      allResults = [...allResults, ...data.results];
    }
    nextUrl = data.next;
  }

  return allResults;
}

// 課題詳細取得
export async function getChallenge(id: number): Promise<ChallengeDetailResponse> {
  return apiCall<ChallengeDetailResponse>(`/${id}/`);
}

// 課題作成
export async function createChallenge(
  data: CreateChallengeRequest
): Promise<Challenge> {
  return apiCall<Challenge>('/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 課題更新
export async function updateChallenge(
  id: number,
  data: UpdateChallengeRequest
): Promise<Challenge> {
  return apiCall<Challenge>(`/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// 課題部分更新
export async function patchChallenge(
  id: number,
  data: Partial<UpdateChallengeRequest>
): Promise<Challenge> {
  return apiCall<Challenge>(`/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// 課題削除
export async function deleteChallenge(id: number): Promise<void> {
  await apiCall<void>(`/${id}/`, {
    method: 'DELETE',
  });
}

// 課題ステータス更新
export async function updateChallengeStatus(
  id: number,
  data: UpdateChallengeStatusRequest
): Promise<Challenge> {
  return apiCall<Challenge>(`/${id}/status/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/** 投稿者のみ。採用候補を確定し、課題 status を completed にする（取り消し不可） */
export async function finalizeAdoption(
  challengeId: number,
  proposalIds: number[]
): Promise<ChallengeDetailResponse> {
  return apiCall<ChallengeDetailResponse>(`/${challengeId}/finalize-adoption/`, {
    method: 'POST',
    body: JSON.stringify({ proposal_ids: proposalIds }),
  });
}

// 課題検索
export async function searchChallenges(
  query: string,
  filters?: Omit<ChallengeFilters, 'search'>
): Promise<ChallengeListResponse> {
  return getChallenges({ ...filters, search: query });
}

// 課題フィルタリング用のヘルパー関数
export const challengeFilters = {
  // 募集中の課題のみ
  open: (): ChallengeFilters => ({ status: 'open' }),
  
  // 特定の投稿者の課題
  byContributor: (contributorId: number): ChallengeFilters => ({ contributor: contributorId }),
  
  // 報酬範囲でフィルタ
  byRewardRange: (min: number, max?: number): ChallengeFilters => ({
    min_reward: min,
    ...(max && { max_reward: max })
  }),
  
  // 期限でフィルタ
  byDeadline: (after?: string, before?: string): ChallengeFilters => ({
    ...(after && { deadline_after: after }),
    ...(before && { deadline_before: before })
  }),
  
  // 複数条件を組み合わせ
  combine: (...filters: ChallengeFilters[]): ChallengeFilters => {
    return filters.reduce((acc, filter) => ({ ...acc, ...filter }), {});
  }
};
