/**
 * モデレーション関連のAPI関数
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// 認証ヘッダーを取得する関数
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

// 報告理由の選択肢
export const REPORT_REASONS = [
  { value: 'spam', label: 'スパム' },
  { value: 'harassment', label: 'ハラスメント' },
  { value: 'inappropriate_content', label: '不適切なコンテンツ' },
  { value: 'violence', label: '暴力的な内容' },
  { value: 'hate_speech', label: 'ヘイトスピーチ' },
  { value: 'copyright', label: '著作権侵害' },
  { value: 'fake_news', label: 'フェイクニュース' },
  { value: 'other', label: 'その他' },
];

// 報告インターフェース
export interface Report {
  id: number;
  reporter: number;
  reporter_username: string;
  content_type: number;
  object_id: number;
  content_type_name: string;
  reason: string;
  description: string;
  status: 'pending' | 'under_review' | 'resolved' | 'dismissed';
  moderator: number | null;
  moderator_username: string | null;
  moderator_notes: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

// 報告作成用インターフェース
export interface CreateReportData {
  content_type: number;
  object_id: number;
  reason: string;
  description?: string;
}

// 報告を作成する関数
export const createReport = async (data: CreateReportData): Promise<Report> => {
  const response = await fetch(`${API_BASE_URL}/moderation/reports/create/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// 報告済みかどうかを確認する関数
export const checkIfReported = async (contentType: number, objectId: number): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/moderation/reports/check/?content_type=${contentType}&object_id=${objectId}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.is_reported || false;
  } catch (error) {
    console.error('報告済み確認エラー:', error);
    return false;
  }
};

// 報告一覧を取得する関数
export const getReports = async (): Promise<Report[]> => {
  const response = await fetch(`${API_BASE_URL}/moderation/reports/`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// ユーザー停止状況を取得する関数
export const getUserSuspensionStatus = async (): Promise<{
  is_suspended: boolean;
  suspension: Record<string, unknown> | null;
}> => {
  const response = await fetch(`${API_BASE_URL}/moderation/suspensions/status/`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// コンテンツタイプを取得する関数（汎用的）
export const getContentType = async (model: string): Promise<number> => {
  const response = await fetch(`${API_BASE_URL}/contenttypes/`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const contentTypes = await response.json();
  const contentType = (contentTypes as { id: number; model: string }[]).find(
    (ct) => ct.model === model
  );
  
  if (!contentType) {
    throw new Error(`Content type not found for model: ${model}`);
  }

  return contentType.id;
};

// コメントを報告する関数
export const reportComment = async (commentId: number, reason: string, description?: string): Promise<Report> => {
  try {
    const contentTypeId = await getContentType('proposalcomment');
    
    return await createReport({
      content_type: contentTypeId,
      object_id: commentId,
      reason,
      description,
    });
  } catch (error) {
    console.error('Error reporting comment:', error);
    throw error;
  }
};

// 提案を報告する関数
export const reportProposal = async (proposalId: number, reason: string, description?: string): Promise<Report> => {
  try {
    const contentTypeId = await getContentType('proposal');
    
    return await createReport({
      content_type: contentTypeId,
      object_id: proposalId,
      reason,
      description,
    });
  } catch (error) {
    console.error('Error reporting proposal:', error);
    throw error;
  }
};

