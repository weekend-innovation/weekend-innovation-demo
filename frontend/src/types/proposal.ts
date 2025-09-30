/**
 * 提案関連の型定義
 */

// 匿名名情報
export interface AnonymousName {
  id: number;
  name: string;
  category: 'animal' | 'plant' | 'inorganic';
}

// 提案の基本情報
export interface Proposal {
  id: number;
  conclusion: string;
  reasoning: string;
  challenge: number;
  challenge_info?: {
    id: number;
    title: string;
    description: string;
    contributor: number;
    reward_amount: number;
    adoption_reward: number;
    required_participants: number;
    deadline: string;
    status: 'open' | 'closed' | 'completed';
  };
  proposer: number;
  proposer_info?: {
    id: number;
    username: string;
    email: string;
    user_type: 'contributor' | 'proposer';
  };
  anonymous_name?: AnonymousName;
  is_anonymous: boolean;
  display_name: string;
  status: 'draft' | 'submitted' | 'under_review' | 'adopted' | 'rejected';
  is_adopted: boolean;
  rating?: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

// 提案一覧表示用（必要最小限の情報）
export interface ProposalListItem {
  id: number;
  conclusion: string;
  reasoning: string;
  challenge_id: number;
  challenge_title: string;
  proposer_name: string;
  anonymous_name_info?: AnonymousName;
  is_anonymous: boolean;
  status: 'draft' | 'submitted' | 'under_review' | 'adopted' | 'rejected';
  is_adopted: boolean;
  rating?: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

// 提案作成リクエスト
export interface CreateProposalRequest {
  challenge: number;
  conclusion: string;
  reasoning: string;
}

// 提案更新リクエスト
export interface UpdateProposalRequest {
  conclusion?: string;
  reasoning?: string;
}

// 提案コメント
export interface ProposalComment {
  id: number;
  proposal: number;
  commenter: number;
  commenter_info?: {
    id: number;
    username: string;
    email: string;
    user_type: 'contributor' | 'proposer';
  };
  target_section: 'reasoning' | 'inference';
  conclusion: string;
  reasoning: string;
  is_deleted: boolean;
  created_at: string;
}

// 提案コメント作成リクエスト
export interface CreateProposalCommentRequest {
  proposal: number;
  target_section: 'reasoning' | 'inference';
  conclusion: string;
  reasoning: string;
}

// 提案評価
export interface ProposalEvaluation {
  id: number;
  proposal: number;
  evaluator: number;
  evaluator_info?: {
    id: number;
    username: string;
    email: string;
    user_type: 'contributor' | 'proposer';
  };
  evaluation: 'yes' | 'maybe' | 'no';
  evaluation_display: string;
  created_at: string;
}

// 提案評価作成リクエスト
export interface CreateProposalEvaluationRequest {
  proposal: number;
  evaluation: 'yes' | 'maybe' | 'no';
}

// 提案一覧取得レスポンス
export interface ProposalListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProposalListItem[];
}

// 提案詳細取得レスポンス
export interface ProposalDetailResponse extends Proposal {}

// 提案コメント一覧取得レスポンス
export interface ProposalCommentListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProposalComment[];
}

// 提案評価一覧取得レスポンス
export interface ProposalEvaluationListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProposalEvaluation[];
}

// API エラーレスポンス
export interface ProposalAPIError {
  detail?: string;
  challenge?: string[];
  conclusion?: string[];
  reasoning?: string[];
  target_section?: string[];
  evaluation?: string[];
  non_field_errors?: string[];
}

// 提案フィルタリング用
export interface ProposalFilters {
  challenge?: number;
  proposer?: number;
  is_adopted?: boolean;
  created_after?: string;
  created_before?: string;
  search?: string;
}

// 提案カード表示用のプロパティ
export interface ProposalCardProps {
  proposal: ProposalListItem;
  showActions?: boolean;
  showEditDelete?: boolean;
  showStatus?: boolean;
  showComments?: boolean;
  showChallengeInfo?: boolean;
  challengeId?: number;
  onView?: (proposal: ProposalListItem) => void;
  onEdit?: (proposal: ProposalListItem) => void;
  onDelete?: (proposal: ProposalListItem) => void;
  onAdopt?: (proposal: ProposalListItem) => void;
  onComments?: (proposal: ProposalListItem) => void;
}

// 提案フォーム用のプロパティ
export interface ProposalFormProps {
  challengeId: number;
  initialData?: Partial<CreateProposalRequest>;
  onSubmit: (data: CreateProposalRequest | UpdateProposalRequest) => void;
  isLoading?: boolean;
  mode: 'create' | 'edit';
}

// 提案コメント表示用のプロパティ
export interface ProposalCommentProps {
  comment: ProposalComment;
  showActions?: boolean;
  onEdit?: (comment: ProposalComment) => void;
  onDelete?: (comment: ProposalComment) => void;
}

// 提案評価表示用のプロパティ
export interface ProposalEvaluationProps {
  evaluation: ProposalEvaluation;
  showActions?: boolean;
  onEdit?: (evaluation: ProposalEvaluation) => void;
  onDelete?: (evaluation: ProposalEvaluation) => void;
}

// ダッシュボード用の統計情報
export interface DashboardStats {
  total_proposals: number;
  adopted_proposals: number;
  total_evaluations: number;
  average_evaluation: number;
  recent_proposals: ProposalListItem[];
  top_evaluated_proposals: ProposalListItem[];
}
