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
  unread_comment_count?: number;
  total_comment_count?: number;
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
  evaluation_count?: number;
  created_at: string;
  updated_at: string;
  unread_comment_count?: number;
  total_comment_count?: number;
  // ユーザー属性（期限切れ課題の解決案一覧用）
  nationality?: string | null;
  gender?: string | null;
  age?: number | null;
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
  reference_comment_id?: number | null;  // 参考ボタンで編集したコメントID（支持率に寄与）
}

// 提案コメント
export interface ProposalComment {
  id: number;
  proposal: number;
  commenter: number;
  commenter_name: string;
  target_section: 'reasoning' | 'inference';
  conclusion: string;
  reasoning: string;
  is_deleted: boolean;
  created_at: string;
  replies?: ProposalCommentReply[];
}

// 提案コメント作成リクエスト
export interface CreateProposalCommentRequest {
  target_section: 'reasoning' | 'inference';
  conclusion: string;
  reasoning: string;
}

// 提案コメント返信
export interface ProposalCommentReply {
  id: number;
  comment: number;
  replier: number;
  replier_name: string;
  content: string;
  is_deleted: boolean;
  created_at: string;
}

// 提案コメント返信作成リクエスト
export interface CreateProposalCommentReplyRequest {
  content: string;
}

// 提案評価
export interface ProposalEvaluation {
  id: number;
  proposal: number;
  evaluator: number;
  evaluator_name: string;
  evaluation: 'yes' | 'maybe' | 'no';
  score: number; // No=2, Maybe=1, Yes=0
  insight_level?: '1' | '2' | '3' | '4' | '5';
  insight_score?: number; // 1-5
  created_at: string;
  updated_at?: string;
}

// 提案評価作成リクエスト
export interface CreateProposalEvaluationRequest {
  evaluation: 'yes' | 'maybe' | 'no';
  insight_level?: '1' | '2' | '3' | '4' | '5';
}

// 提案参考
export interface ProposalReference {
  id: number;
  proposal: number;
  referencer: number;
  referencer_name: string;
  notes: string;
  created_at: string;
}

// 提案参考作成リクエスト
export interface CreateProposalReferenceRequest {
  notes?: string;
}

// 提案一覧取得レスポンス
export interface ProposalListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProposalListItem[];
}

// 提案詳細取得レスポンス（コメント・評価情報を含む）
export interface ProposalDetailResponse extends Proposal {
  comments: ProposalComment[];
  evaluations: ProposalEvaluation[];
  user_evaluation?: ProposalEvaluation;
  user_reference?: ProposalReference;
}

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
  readOnlyComments?: boolean; // 期限切れ課題用：コメント閲覧のみ（投稿・返信・通報不可）
  showChallengeInfo?: boolean;
  showUserAttributes?: boolean; // 期限切れ課題用：ユーザー属性（国旗、性別、年齢）を表示
  useServerDataOnly?: boolean; // 分析サマリー用：localStorageの編集データを無視し、サーバーデータのみ表示
  challengeId?: number;
  currentPhase?: 'proposal' | 'edit' | 'evaluation' | 'closed'; // 課題の現在のフェーズ
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


// ダッシュボード用の統計情報
export interface DashboardStats {
  total_proposals: number;
  adopted_proposals: number;
  total_evaluations: number;
  average_evaluation: number;
  recent_proposals: ProposalListItem[];
  top_evaluated_proposals: ProposalListItem[];
}

// 評価・コメント機能用のコンポーネントプロパティ
export interface ProposalEvaluationProps {
  proposalId: number;
  userEvaluation?: ProposalEvaluation;
  onEvaluate: (proposalId: number, evaluation: 'yes' | 'maybe' | 'no', insightLevel?: '1' | '2' | '3' | '4' | '5') => void;
  isEvaluating?: boolean;
}

export interface ProposalCommentListProps {
  proposalId: number;
  proposal: ProposalListItem;
  proposalState?: ProposalListItem;
  comments: ProposalComment[];
  onAddComment: (comment: CreateProposalCommentRequest) => void;
  onReply: (commentId: number, reply: CreateProposalCommentReplyRequest) => void;
  onEdit: (proposalId: number, data: { conclusion: string; reasoning: string }) => void;
  onReference?: (commentId: number) => void;
  isAddingComment?: boolean;
  isReplying?: boolean;
  isEditing?: boolean;
  editingCommentId?: number | null;
  setEditingCommentId?: (commentId: number | null) => void;
  canComment?: boolean;
  canReply?: boolean;
  canReference?: boolean;
}

export interface ProposalCommentFormProps {
  onSubmit: (comment: CreateProposalCommentRequest) => void;
  isLoading?: boolean;
}

export interface ProposalCommentReplyFormProps {
  commentId: number;
  onSubmit: (reply: CreateProposalCommentReplyRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

// 参考ログ
export interface ReferenceLog {
  id: string;
  commentId: number;
  commentConclusion: string;
  editedAt: string;
}
