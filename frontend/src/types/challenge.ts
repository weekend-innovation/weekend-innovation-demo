/**
 * 課題関連の型定義
 */

// 課題ステータス
export type ChallengeStatus = 'open' | 'closed' | 'completed';

// 課題フェーズ
export type ChallengePhase = 'proposal' | 'edit' | 'evaluation' | 'closed';

// 課題の基本情報
export interface Challenge {
  id: number;
  title: string;
  description: string;
  contributor: number;
  contributor_info?: {
    id: number;
    username: string;
    email: string;
    user_type: 'contributor' | 'proposer';
  };
  reward_amount: number;
  adoption_reward: number;
  required_participants: number;
  deadline: string;
  proposal_deadline?: string;
  edit_deadline?: string;
  evaluation_deadline?: string;
  current_phase?: ChallengePhase;
  phase_display?: string;
  status: ChallengeStatus;
  created_at: string;
  updated_at: string;
  has_completed_all_evaluations?: boolean;
}

// 課題一覧表示用（必要最小限の情報）
export interface ChallengeListItem {
  id: number;
  title: string;
  description: string;
  contributor_name: string;
  reward_amount: number;
  adoption_reward: number;
  required_participants: number;
  deadline: string;
  proposal_deadline?: string;
  edit_deadline?: string;
  evaluation_deadline?: string;
  current_phase?: ChallengePhase;
  phase_display?: string;
  status: ChallengeStatus;
  created_at: string;
  has_completed_all_evaluations?: boolean;
  has_proposed?: boolean;
  priority?: number;
}

// 課題作成リクエスト
export interface CreateChallengeRequest {
  title: string;
  description: string;
  reward_amount: number;
  adoption_reward: number;
  required_participants: number;
  deadline: string;
}

// 課題更新リクエスト
export interface UpdateChallengeRequest {
  title?: string;
  description?: string;
  reward_amount?: number;
  adoption_reward?: number;
  required_participants?: number;
  deadline?: string;
  status?: ChallengeStatus;
}

// 課題ステータス更新リクエスト
export interface UpdateChallengeStatusRequest {
  status: ChallengeStatus;
}

// 課題一覧取得レスポンス
export interface ChallengeListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ChallengeListItem[];
}

// 課題詳細取得レスポンス
export type ChallengeDetailResponse = Challenge;

// API エラーレスポンス
export interface ChallengeAPIError {
  detail?: string;
  title?: string[];
  description?: string[];
  reward_amount?: string[];
  adoption_reward?: string[];
  required_participants?: string[];
  deadline?: string[];
  status?: string[];
  non_field_errors?: string[];
}

// 課題フィルタリング用
export interface ChallengeFilters {
  status?: ChallengeStatus;
  contributor?: number;
  min_reward?: number;
  max_reward?: number;
  deadline_after?: string;
  deadline_before?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

// 課題カード表示用のプロパティ
export interface ChallengeCardProps {
  challenge: ChallengeListItem;
  showActions?: boolean;
  userType?: 'contributor' | 'proposer';
  isProposed?: boolean;
  onView?: (challenge: ChallengeListItem) => void;
  onEdit?: (challenge: ChallengeListItem) => void;
  onDelete?: (challenge: ChallengeListItem) => void;
}

// 課題フォーム用のプロパティ
export interface ChallengeFormProps {
  initialData?: Partial<CreateChallengeRequest>;
  onSubmit: (data: CreateChallengeRequest | UpdateChallengeRequest) => void;
  isLoading?: boolean;
  mode: 'create' | 'edit';
}
