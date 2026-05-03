/**
 * 提案者向け分析結果コンポーネント
 * 自分の提案の分析スコアと成果を表示
 */
import React from 'react';
import ProposalCard from '../proposals/ProposalCard';
import type { ProposalListItem } from '../../types/proposal';
import { getGenderDisplay } from '../../lib/countryFlags';
import CountryFlag from '../common/CountryFlag';
import { CLUSTER_COLORS } from './ProposalClusterMap';

interface ProposalInsight {
  id: number;
  proposal_id: number;
  innovation_score: number;
  insightfulness_score: number;
  impact_score: number;
  key_themes: string[];
  strengths: string[];
  concerns: string[];
  is_selected?: boolean;
  nationality?: string | null;
  gender?: string | null;
  age?: number | null;
}

interface CommonTheme {
  theme: string;
  frequency: number;
  percentage: number;
}

interface ChallengeAnalysisData {
  id: number;
  status: string;
  status_display: string;
  total_proposals: number;
  unique_proposers: number;
  common_themes: CommonTheme[];
  executive_summary?: string;
  detailed_analysis?: string;
  analyzed_at: string | null;
  top_proposals?: {
    originality: ProposalInsight | null;
    insightfulness: ProposalInsight | null;
    impact: ProposalInsight | null;
  };
}

interface ClusteringResult {
  coordinates: Array<{
    proposal_id: number;
    x: number;
    y: number;
    cluster: number;
    comment_count: number;
  }>;
  cluster_info: Array<{
    cluster_id: number;
    size: number;
    theme: string;
  }>;
  total_clusters: number;
}

interface ProposerAnalysisSummaryProps {
  analysis: ChallengeAnalysisData;
  myInsight: ProposalInsight | null;
  myProposalId: number;
  proposals: ProposalListItem[];
  clusteringData?: ClusteringResult | null;
  isLoading?: boolean;
}

const ProposerAnalysisSummary: React.FC<ProposerAnalysisSummaryProps> = ({
  analysis,
  myInsight,
  myProposalId,
  proposals,
  clusteringData = null,
  isLoading = false
}) => {
  // 提案IDからクラスタ番号を取得する関数
  const getProposalCluster = (proposalId: number): number => {
    if (!clusteringData || !clusteringData.coordinates) {
      return 0;
    }
    const coordinate = clusteringData.coordinates.find((c) => c.proposal_id === proposalId);
    const cluster = coordinate?.cluster ?? 0;
    return cluster;
  };

  // クラスタ色から薄い色を生成する関数（投稿者ユーザーの散布図と同じ）
  const getClusterLightColor = (clusterIndex: number): string => {
    const baseColor = CLUSTER_COLORS[clusterIndex % CLUSTER_COLORS.length];
    const r = parseInt(baseColor.slice(1, 3), 16);
    const g = parseInt(baseColor.slice(3, 5), 16);
    const b = parseInt(baseColor.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.15)`; // 15%の透明度
  };
  
  // クラスタ色から境界線の色を生成する関数（投稿者ユーザーの散布図と同じ）
  const getClusterBorderColor = (clusterIndex: number): string => {
    const baseColor = CLUSTER_COLORS[clusterIndex % CLUSTER_COLORS.length];
    const r = parseInt(baseColor.slice(1, 3), 16);
    const g = parseInt(baseColor.slice(3, 5), 16);
    const b = parseInt(baseColor.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.4)`; // 40%の透明度
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis || !myInsight) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500">
          <p>分析結果がまだ生成されていません。</p>
          <p className="text-sm mt-2">課題の期間が満了すると、自動的に分析が行われます。</p>
        </div>
      </div>
    );
  }

  // スコアを数値でなく「大」「中」「小」で表示（実際の数値は出さない）
  const getScoreLabel = (score: number): string => {
    if (score >= 0.6) return '大';
    if (score >= 0.3) return '中';
    return '小';
  };

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* ヘッダー */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              分析結果
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              課題の全{analysis.total_proposals}件の提案から分析された、あなたの提案の評価です
            </p>
          </div>
          {analysis.analyzed_at && (
            <span className="text-xs text-gray-500">
              分析日: {new Date(analysis.analyzed_at).toLocaleDateString('ja-JP')}
            </span>
          )}
        </div>
      </div>

      <div className="px-6 py-6 space-y-6">
        {/* エグゼクティブサマリー */}
        {analysis.executive_summary && analysis.executive_summary.trim() && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              📋 サマリー
            </h3>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {analysis.executive_summary}
            </p>
          </div>
        )}

        {/* スコア概要（数値は表示せず、ラベルを上に・評価は大/中/小） */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📊 総合評価
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {/* 革新性 */}
            <div className={`text-center p-4 rounded-lg border-2 ${
              myInsight.innovation_score >= 0.6 ? 'bg-green-50 border-green-300' :
              myInsight.innovation_score >= 0.3 ? 'bg-yellow-50 border-yellow-300' :
              'bg-gray-50 border-gray-300'
            }`}>
              <div className="text-sm font-medium text-gray-700 mb-2">革新性</div>
              <div className={`text-2xl font-bold ${
                myInsight.innovation_score >= 0.6 ? 'text-green-600' :
                myInsight.innovation_score >= 0.3 ? 'text-yellow-600' :
                'text-gray-600'
              }`}>
                {getScoreLabel(myInsight.innovation_score)}
              </div>
            </div>

            {/* 支持率 */}
            <div className={`text-center p-4 rounded-lg border-2 ${
              myInsight.insightfulness_score >= 0.6 ? 'bg-green-50 border-green-300' :
              myInsight.insightfulness_score >= 0.3 ? 'bg-yellow-50 border-yellow-300' :
              'bg-gray-50 border-gray-300'
            }`}>
              <div className="text-sm font-medium text-gray-700 mb-2">支持率</div>
              <div className={`text-2xl font-bold ${
                myInsight.insightfulness_score >= 0.6 ? 'text-green-600' :
                myInsight.insightfulness_score >= 0.3 ? 'text-yellow-600' :
                'text-gray-600'
              }`}>
                {getScoreLabel(myInsight.insightfulness_score)}
              </div>
            </div>

            {/* 影響度 */}
            <div className={`text-center p-4 rounded-lg border-2 ${
              myInsight.impact_score >= 0.6 ? 'bg-green-50 border-green-300' :
              myInsight.impact_score >= 0.3 ? 'bg-yellow-50 border-yellow-300' :
              'bg-gray-50 border-gray-300'
            }`}>
              <div className="text-sm font-medium text-gray-700 mb-2">影響度</div>
              <div className={`text-2xl font-bold ${
                myInsight.impact_score >= 0.6 ? 'text-green-600' :
                myInsight.impact_score >= 0.3 ? 'text-yellow-600' :
                'text-gray-600'
              }`}>
                {getScoreLabel(myInsight.impact_score)}
              </div>
            </div>
          </div>
          <div className="mt-4 bg-gray-50 p-4 rounded-lg text-center">
            <span className="text-sm font-medium text-gray-700">総合 </span>
            <span className={`text-lg font-bold ${
              (myInsight.innovation_score + myInsight.insightfulness_score + myInsight.impact_score) / 3 >= 0.6 ? 'text-green-600' :
              (myInsight.innovation_score + myInsight.insightfulness_score + myInsight.impact_score) / 3 >= 0.3 ? 'text-yellow-600' :
              'text-gray-600'
            }`}>
              {getScoreLabel((myInsight.innovation_score + myInsight.insightfulness_score + myInsight.impact_score) / 3)}
            </span>
          </div>
        </div>

        {/* 各カテゴリーのトップ解決案（散布図の下に表示） */}
        {analysis.top_proposals && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              🏆 各カテゴリーのトップ解決案
            </h3>
            <div className="space-y-6">
              {analysis.top_proposals.originality && (() => {
                const proposal = proposals.find(p => p.id === analysis.top_proposals?.originality?.proposal_id);
                const topData = analysis.top_proposals.originality;
                const isMyProposal = topData.proposal_id === myProposalId;
                const clusterIndex = getProposalCluster(topData.proposal_id);
                const bgColor = getClusterLightColor(clusterIndex);
                const borderColor = getClusterBorderColor(clusterIndex);
                return proposal && (
                  <div>
                    <div
                      className="px-4 py-2 rounded-t-lg border"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h4 className="text-sm font-semibold text-gray-900">
                            ⭐ 革新性が最も高い解決案
                            {isMyProposal && <span className="ml-2 text-gray-600">（あなたの提案）</span>}
                          </h4>
                          {topData.is_selected && (topData.nationality || topData.gender || topData.age) && (
                            <div className="flex items-center gap-2">
                              {topData.nationality && (
                                <CountryFlag countryCode={topData.nationality} size="small" />
                              )}
                              {topData.gender && (
                                <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                                  {getGenderDisplay(topData.gender)}
                                </span>
                              )}
                              {topData.age != null && (
                                <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                                  {topData.age}歳
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div
                      className="border border-t-0 rounded-b-lg p-2"
                      style={{ borderColor: borderColor }}
                    >
                      <ProposalCard
                        proposal={proposal}
                        showActions={false}
                        showStatus={false}
                        showComments={true}
                        readOnlyComments={true}
                        showChallengeInfo={false}
                      />
                    </div>
                  </div>
                );
              })()}

              {analysis.top_proposals.insightfulness && (() => {
                const proposal = proposals.find(p => p.id === analysis.top_proposals?.insightfulness?.proposal_id);
                const topData = analysis.top_proposals.insightfulness;
                const isMyProposal = topData.proposal_id === myProposalId;
                const clusterIndex = getProposalCluster(topData.proposal_id);
                const bgColor = getClusterLightColor(clusterIndex);
                const borderColor = getClusterBorderColor(clusterIndex);
                return proposal && (
                  <div>
                    <div
                      className="px-4 py-2 rounded-t-lg border"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h4 className="text-sm font-semibold text-gray-900">
                            💡 最も支持されている解決案
                            {isMyProposal && <span className="ml-2 text-gray-600">（あなたの提案）</span>}
                          </h4>
                          {topData.is_selected && (topData.nationality || topData.gender || topData.age) && (
                            <div className="flex items-center gap-2">
                              {topData.nationality && (
                                <CountryFlag countryCode={topData.nationality} size="small" />
                              )}
                              {topData.gender && (
                                <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                                  {getGenderDisplay(topData.gender)}
                                </span>
                              )}
                              {topData.age != null && (
                                <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                                  {topData.age}歳
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <span className="text-xs bg-white px-2 py-1 rounded font-medium text-gray-700 border border-gray-300">
                          支持率: {Math.round(topData.insightfulness_score * 100)}%
                        </span>
                      </div>
                    </div>
                    <div
                      className="border border-t-0 rounded-b-lg p-2"
                      style={{ borderColor: borderColor }}
                    >
                      <ProposalCard
                        proposal={proposal}
                        showActions={false}
                        showStatus={false}
                        showComments={true}
                        readOnlyComments={true}
                        showChallengeInfo={false}
                      />
                    </div>
                  </div>
                );
              })()}

              {analysis.top_proposals.impact && (() => {
                const proposal = proposals.find(p => p.id === analysis.top_proposals?.impact?.proposal_id);
                const topData = analysis.top_proposals.impact;
                const isMyProposal = topData.proposal_id === myProposalId;
                const clusterIndex = getProposalCluster(topData.proposal_id);
                const bgColor = getClusterLightColor(clusterIndex);
                const borderColor = getClusterBorderColor(clusterIndex);
                return proposal && (
                  <div>
                    <div
                      className="px-4 py-2 rounded-t-lg border"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h4 className="text-sm font-semibold text-gray-900">
                            🔥 影響度が最も高い解決案
                            {isMyProposal && <span className="ml-2 text-gray-600">（あなたの提案）</span>}
                          </h4>
                          {topData.is_selected && (topData.nationality || topData.gender || topData.age) && (
                            <div className="flex items-center gap-2">
                              {topData.nationality && (
                                <CountryFlag countryCode={topData.nationality} size="small" />
                              )}
                              {topData.gender && (
                                <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                                  {getGenderDisplay(topData.gender)}
                                </span>
                              )}
                              {topData.age != null && (
                                <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                                  {topData.age}歳
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div
                      className="border border-t-0 rounded-b-lg p-2"
                      style={{ borderColor: borderColor }}
                    >
                      <ProposalCard
                        proposal={proposal}
                        showActions={false}
                        showStatus={false}
                        showComments={true}
                        readOnlyComments={true}
                        showChallengeInfo={false}
                      />
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProposerAnalysisSummary;
