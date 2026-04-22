/**
 * 提案関連APIサービス
 */
import { tokenManager } from './api';
import type {
  Proposal,
  ProposalListItem,
  ProposalListResponse,
  CreateProposalRequest,
  UpdateProposalRequest,
  ProposalFilters,
  ProposalDetailResponse,
  ProposalComment,
  ProposalCommentListResponse,
  CreateProposalCommentRequest,
  ProposalCommentReply,
  CreateProposalCommentReplyRequest,
  ProposalEvaluation,
  CreateProposalEvaluationRequest,
  ProposalReference,
  CreateProposalReferenceRequest
} from '../types/proposal';

// API ベースURL
const API_BASE_URL = 'http://localhost:8000/api/proposals';

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
    
    let errorData: Record<string, unknown> = {};
    try {
      errorData = await response.json();
    } catch (e) {
      console.error('JSON parse error:', e);
    }
    
    // 404エラーの場合は評価データが存在しないことを意味するため、ログ出力を抑制
    if (response.status !== 404 || !endpoint.includes('/evaluation/')) {
      console.error('API Error Details:', {
        status: response.status,
        statusText: response.statusText,
        url: response.url,
        errorData,
        errorString: JSON.stringify(errorData, null, 2),
        endpoint: endpoint,
        method: config.method || 'GET'
      });
    }
    
    const detail = typeof errorData.detail === 'string' ? errorData.detail : undefined;
    throw new Error(detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

// 提案一覧取得
export async function getProposals(
  filters?: ProposalFilters
): Promise<ProposalListResponse> {
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
  
  return apiCall<ProposalListResponse>(endpoint);
}

// 特定課題の提案一覧取得
export async function getProposalsByChallenge(
  challengeId: number
): Promise<ProposalListResponse> {
  return apiCall<ProposalListResponse>(`/challenge/${challengeId}/`);
}

// 提案詳細取得
export async function getProposal(id: number): Promise<Proposal> {
  return apiCall<Proposal>(`/${id}/`);
}

// ユーザーの特定課題への提案状況確認
export async function getUserProposalForChallenge(
  challengeId: number
): Promise<Proposal | null> {
  try {
    const proposals = await apiCall<Proposal[] | { results: Proposal[] }>(`/user-challenge/${challengeId}/`);
    if (Array.isArray(proposals)) {
      return proposals.length > 0 ? proposals[0] : null;
    }
    return proposals.results.length > 0 ? proposals.results[0] : null;
  } catch (error) {
    console.log('No proposal found for this challenge:', error);
    return null;
  }
}

// 提案作成
export async function createProposal(
  data: CreateProposalRequest
): Promise<Proposal> {
  return apiCall<Proposal>('/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 提案更新
export async function updateProposal(
  id: number,
  data: UpdateProposalRequest
): Promise<Proposal> {
  return apiCall<Proposal>(`/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// 提案部分更新
export async function patchProposal(
  id: number,
  data: Partial<UpdateProposalRequest>
): Promise<Proposal> {
  return apiCall<Proposal>(`/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// 提案削除
export async function deleteProposal(id: number): Promise<void> {
  await apiCall<void>(`/${id}/`, {
    method: 'DELETE',
  });
}

// 提案詳細取得（コメント・評価情報を含む）
export async function getProposalWithComments(id: number): Promise<ProposalDetailResponse> {
  return apiCall<ProposalDetailResponse>(`/${id}/with-comments/`);
}

// 提案コメント一覧取得
export async function getProposalComments(proposalId: number): Promise<ProposalCommentListResponse> {
  return apiCall<ProposalCommentListResponse>(`/${proposalId}/comments/`);
}

// 提案コメント作成
export async function createProposalComment(
  proposalId: number,
  data: CreateProposalCommentRequest
): Promise<ProposalComment> {
  return apiCall<ProposalComment>(`/${proposalId}/comments/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 提案評価作成
export async function createProposalEvaluation(
  proposalId: number,
  data: CreateProposalEvaluationRequest
): Promise<ProposalEvaluation> {
  console.log('評価作成API呼び出し:', { proposalId, data });
  return apiCall<ProposalEvaluation>(`/${proposalId}/evaluate/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 提案評価取得
export async function getProposalEvaluation(
  proposalId: number
): Promise<ProposalEvaluation | null> {
  try {
    return await apiCall<ProposalEvaluation>(`/${proposalId}/evaluation/`);
  } catch (error) {
    // 404エラーの場合は評価データが存在しない（ログ出力を抑制）
    if (error instanceof Error && (error.message.includes('404') || error.message.includes('評価データが見つかりません'))) {
      console.log('評価データ未作成（正常）:', proposalId);
      return null;
    }
    throw error;
  }
}

// コメント返信作成
export async function createProposalCommentReply(
  commentId: number,
  data: CreateProposalCommentReplyRequest
): Promise<ProposalCommentReply> {
  return apiCall<ProposalCommentReply>(`/comments/${commentId}/reply/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 提案参考作成
export async function createProposalReference(
  proposalId: number,
  data: CreateProposalReferenceRequest
): Promise<ProposalReference> {
  return apiCall<ProposalReference>(`/${proposalId}/reference/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 解決案採用の設定（投稿者のみ、期限切れ課題）
export async function setProposalAdopted(
  proposalId: number,
  isAdopted: boolean
): Promise<ProposalListItem> {
  return apiCall<ProposalListItem>(`/${proposalId}/adopt/`, {
    method: 'PATCH',
    body: JSON.stringify({ is_adopted: isAdopted }),
  });
}