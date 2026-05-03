/**
 * 課題分析API関数
 */
import { tokenManager } from './api';

/** 他モジュールと同様、ベースに `/api` まで含める（重複で /api/api にならないようにする） */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// 分析結果の型定義
export interface CommonTheme {
  theme: string;
  frequency: number;
  percentage: number;
}

// 提案洞察の型定義
export interface ProposalInsight {
  id: number;
  proposal_id: number;
  innovation_score: number;
  insightfulness_score: number;
  impact_score: number;
  key_themes: string[];
  strengths: string[];
  concerns: string[];
  created_at: string;
}

export interface InnovativeSolution {
  proposal_id: number;
  innovation_score: number;
  key_innovations: string[];
  summary: string;
}

export interface FeasibilityAnalysis {
  distribution: {
    high: number;
    medium: number;
    low: number;
  };
  scores: Array<{
    proposal_id: number;
    score: number;
    level: string;
  }>;
}

export interface ChallengeAnalysisData {
  id: number;
  challenge: number;
  status: string;
  status_display: string;
  total_proposals: number;
  unique_proposers: number;
  common_themes: CommonTheme[];
  innovative_solutions: InnovativeSolution[];
  feasibility_analysis?: FeasibilityAnalysis;  // オプショナル（非推奨）
  executive_summary: string;
  detailed_analysis: string;
  recommendations: string;
  created_at: string;
  updated_at: string;
  analyzed_at: string | null;
  insights?: ProposalInsight[];
  top_proposals?: {
    originality: ProposalInsight | null;
    insightfulness: ProposalInsight | null;
    impact: ProposalInsight | null;
  };
}

export interface AnalysisStatus {
  status: string;
  analyzed_at: string | null;
  total_proposals: number;
  unique_proposers: number;
}

/**
 * 課題の分析結果を取得
 */
export const getChallengeAnalysis = async (challengeId: number): Promise<ChallengeAnalysisData | null> => {
  try {
    const token = tokenManager.getAccessToken();
    if (!token) {
      throw new Error('認証トークンがありません');
    }

    const response = await fetch(`${API_BASE_URL}/analytics/challenges/${challengeId}/analysis/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`分析結果の取得に失敗しました: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('分析結果取得エラー:', error);
    throw error;
  }
};

/**
 * 分析ステータスを取得
 */
export const getAnalysisStatus = async (challengeId: number): Promise<AnalysisStatus> => {
  try {
    const token = tokenManager.getAccessToken();
    if (!token) {
      throw new Error('認証トークンがありません');
    }

    const response = await fetch(`${API_BASE_URL}/analytics/challenges/${challengeId}/analysis/status/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`分析ステータスの取得に失敗しました: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('分析ステータス取得エラー:', error);
    throw error;
  }
};

/**
 * 分析を手動実行
 */
export const triggerAnalysis = async (challengeId: number): Promise<ChallengeAnalysisData> => {
  try {
    const token = tokenManager.getAccessToken();
    if (!token) {
      throw new Error('認証トークンがありません');
    }

    const response = await fetch(`${API_BASE_URL}/analytics/challenges/${challengeId}/analyze/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `分析の実行に失敗しました: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('分析実行エラー:', error);
    throw error;
  }
};

/**
 * 特定の提案の洞察データを取得（提案者向け）
 */
export const getMyProposalInsight = async (challengeId: number, proposalId: number): Promise<ProposalInsight | null> => {
  try {
    // まず分析結果を取得して、その中から自分の提案の洞察を探す
    const analysis = await getChallengeAnalysis(challengeId);
    if (!analysis) {
      return null;
    }

    // insightsの中から自分の提案IDに一致するものを探す
    const insights = analysis.insights || [];
    const myInsight = insights.find((insight: ProposalInsight) => insight.proposal_id === proposalId);
    
    return myInsight || null;
  } catch (error) {
    console.error('提案洞察取得エラー:', error);
    return null;
  }
};
