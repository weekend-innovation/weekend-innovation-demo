export type QaStatus = 'pending' | 'answered' | 'hidden';

export interface QaQuestion {
  id: number;
  asked_by: number | null;
  asked_by_username: string;
  question_text: string;
  answer_text: string;
  answered_by: number | null;
  answered_by_username: string;
  answered_at: string | null;
  status: QaStatus;
  is_public: boolean;
  /** 公開済みQ&AのAPI応答では null になることがある */
  created_at: string | null;
  updated_at: string;
}

export interface QaCreateRequest {
  question_text: string;
}

