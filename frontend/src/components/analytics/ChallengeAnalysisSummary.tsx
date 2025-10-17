/**
 * 課題分析結果サマリーコンポーネント
 * 期限切れ課題の分析結果を表示
 */
'use client';

import React, { useState } from 'react';
import type { ProposalListItem } from '../../types/proposal';
import ProposalClusterMap, { CLUSTER_COLORS } from './ProposalClusterMap';
import ProposalCard from '../proposals/ProposalCard';
import { getGenderDisplay } from '../../lib/countryFlags';
import CountryFlag from '../common/CountryFlag';

interface CommonTheme {
  theme: string;
  frequency: number;
  percentage: number;
}

interface InnovativeSolution {
  proposal_id: number;
  innovation_score: number;
  key_innovations: string[];
  summary: string;
}

interface FeasibilityAnalysis {
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

interface ProposalInsight {
  id: number;
  proposal_id: number;
  innovation_score: number;
  insightfulness_score: number;
  impact_score: number;
  key_themes: string[];
  strengths: string[];
  concerns: string[];
  created_at: string;
  is_selected?: boolean;
  nationality?: string | null;
  gender?: string | null;
  age?: number | null;
}

interface ChallengeAnalysisData {
  id: number;
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
  analyzed_at: string | null;
  insights?: ProposalInsight[];
  top_proposals?: {
    originality: ProposalInsight | null;
    insightfulness: ProposalInsight | null;
    impact: ProposalInsight | null;
  };
}

interface ChallengeAnalysisSummaryProps {
  analysis: ChallengeAnalysisData | null;
  proposals: ProposalListItem[];
  challengeId: number;
  isLoading?: boolean;
  onClusteringDataLoaded?: (data: any) => void;
}

const ChallengeAnalysisSummary: React.FC<ChallengeAnalysisSummaryProps> = ({
  analysis,
  proposals,
  challengeId,
  isLoading = false,
  onClusteringDataLoaded
}) => {
  // 選択された解決案のID
  const [selectedProposalId, setSelectedProposalId] = useState<number | null>(null);
  // 選択された解決案の属性情報（クラスタリングデータから取得）
  const [selectedProposalAttributes, setSelectedProposalAttributes] = useState<{
    nationality?: string | null;
    gender?: string | null;
    age?: number | null;
    is_selected?: boolean;
  } | null>(null);
  // クラスタリングデータ（散布図から取得）
  const [clusteringData, setClusteringData] = useState<any>(null);
  
  // 選択された解決案の詳細
  const selectedProposal = selectedProposalId 
    ? proposals.find(p => p.id === selectedProposalId) 
    : null;
  
  // 提案IDからクラスタ情報を取得する関数
  const getProposalCluster = (proposalId: number): number => {
    if (!clusteringData || !clusteringData.coordinates) return 0;
    const coordinate = clusteringData.coordinates.find((c: any) => c.proposal_id === proposalId);
    return coordinate?.cluster ?? 0;
  };
  
  // クラスタ色から薄い色を生成する関数
  const getClusterLightColor = (cluster: number): string => {
    const baseColor = CLUSTER_COLORS[cluster % CLUSTER_COLORS.length];
    // 16進数カラーをRGBに変換して透明度を下げる
    const r = parseInt(baseColor.slice(1, 3), 16);
    const g = parseInt(baseColor.slice(3, 5), 16);
    const b = parseInt(baseColor.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.15)`; // 15%の透明度
  };
  
  // クラスタ色から境界線の色を生成する関数
  const getClusterBorderColor = (cluster: number): string => {
    const baseColor = CLUSTER_COLORS[cluster % CLUSTER_COLORS.length];
    const r = parseInt(baseColor.slice(1, 3), 16);
    const g = parseInt(baseColor.slice(3, 5), 16);
    const b = parseInt(baseColor.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.4)`; // 40%の透明度
  };
  
  // デバッグ：選択時にログ出力
  React.useEffect(() => {
    if (selectedProposalId) {
      console.log('選択された解決案ID:', selectedProposalId);
      console.log('提案一覧の解決案ID:', proposals.map(p => p.id));
      console.log('見つかった解決案:', selectedProposal ? `ID ${selectedProposal.id}` : '見つかりません');
    }
  }, [selectedProposalId, proposals, selectedProposal]);
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

  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500">
          <p>分析結果がありません。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* ヘッダー */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            解決案分析結果
          </h2>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              analysis.status === 'completed' 
                ? 'bg-green-100 text-green-800'
                : analysis.status === 'processing'
                ? 'bg-blue-100 text-blue-800'
                : analysis.status === 'failed'
                ? 'bg-red-100 text-red-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {analysis.status_display}
            </span>
            {analysis.analyzed_at && (
              <span className="text-sm text-gray-500">
                分析完了: {new Date(analysis.analyzed_at).toLocaleDateString('ja-JP')}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 統計情報 */}
      <div className="px-6 py-4 bg-gray-50">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {analysis.total_proposals}
            </div>
            <div className="text-sm text-gray-600">総提案数</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {analysis.unique_proposers}
            </div>
            <div className="text-sm text-gray-600">提案者数</div>
          </div>
        </div>
      </div>

      <div className="px-6 py-4 space-y-6">
        {/* AIクラスタリングマップ */}
        <ProposalClusterMap
          challengeId={challengeId}
          proposals={proposals}
          onProposalClick={(proposalId, attributes) => {
            console.log('解決案クリック:', { proposalId, attributes });
            setSelectedProposalId(proposalId === selectedProposalId ? null : proposalId);
            setSelectedProposalAttributes(attributes || null);
          }}
          selectedProposalId={selectedProposalId}
          onClusteringDataLoaded={(data) => {
            setClusteringData(data);
            if (onClusteringDataLoaded) {
              onClusteringDataLoaded(data);
            }
          }}
        />

        {/* 選択された解決案の詳細表示 */}
        {selectedProposal && (
          <div className="border-2 border-blue-500 rounded-lg animate-pulse-once">
            <div className="bg-gray-100 px-4 py-2 rounded-t-lg flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-semibold text-gray-900">
                  選択中の解決案
                </h3>
                {/* 選出されたユーザーの属性情報を表示 */}
                {selectedProposalAttributes?.is_selected && (
                  <div className="flex items-center gap-2 text-sm">
                    {selectedProposalAttributes.nationality && (
                      <CountryFlag countryCode={selectedProposalAttributes.nationality} size="medium" />
                    )}
                    {selectedProposalAttributes.gender && (
                      <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                        {getGenderDisplay(selectedProposalAttributes.gender)}
                      </span>
                    )}
                    {selectedProposalAttributes.age && (
                      <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                        {selectedProposalAttributes.age}歳
                      </span>
                    )}
                  </div>
                )}
              </div>
              <button
                onClick={() => setSelectedProposalId(null)}
                className="text-gray-700 hover:text-gray-900 text-sm font-medium"
              >
                ✕ 閉じる
              </button>
            </div>
            <div className="p-2">
              <ProposalCard
                key={selectedProposal.id}
                proposal={selectedProposal}
                showActions={false}
                showStatus={false}
                showComments={true}
                readOnlyComments={true}
                showChallengeInfo={false}
              />
            </div>
          </div>
        )}

        {/* 分析サマリー - 統合版 */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📊 分析サマリー
          </h3>
          
          {/* トップ提案をProposalCardで表示 */}
          {analysis.top_proposals && (
            <div className="space-y-6">
              {/* 独創性トップ */}
              {analysis.top_proposals.originality && (() => {
                const proposal = proposals.find(p => p.id === analysis.top_proposals?.originality?.proposal_id);
                const topData = analysis.top_proposals.originality;
                const cluster = getProposalCluster(topData.proposal_id);
                const bgColor = getClusterLightColor(cluster);
                const borderColor = getClusterBorderColor(cluster);
                return proposal && (
                  <div>
                    <div 
                      className="px-4 py-2 rounded-t-lg border"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h4 className="text-sm font-semibold text-gray-900">⭐ 最も独創的な解決案</h4>
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
                              {topData.age && (
                                <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                                  {topData.age}歳
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <span className="text-xs bg-white px-2 py-1 rounded font-medium text-gray-700 border border-gray-300">
                          独創性: {Math.round(topData.innovation_score * 100)}%
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
              
              {/* 支持率トップ */}
              {analysis.top_proposals.insightfulness && (() => {
                const proposal = proposals.find(p => p.id === analysis.top_proposals?.insightfulness?.proposal_id);
                const topData = analysis.top_proposals.insightfulness;
                const cluster = getProposalCluster(topData.proposal_id);
                const bgColor = getClusterLightColor(cluster);
                const borderColor = getClusterBorderColor(cluster);
                return proposal && (
                  <div>
                    <div 
                      className="px-4 py-2 rounded-t-lg border"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h4 className="text-sm font-semibold text-gray-900">💡 最も支持されている解決案</h4>
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
                              {topData.age && (
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
              
              {/* 影響度トップ */}
              {analysis.top_proposals.impact && (() => {
                const proposal = proposals.find(p => p.id === analysis.top_proposals?.impact?.proposal_id);
                const topData = analysis.top_proposals.impact;
                const cluster = getProposalCluster(topData.proposal_id);
                const bgColor = getClusterLightColor(cluster);
                const borderColor = getClusterBorderColor(cluster);
                return proposal && (
                  <div>
                    <div 
                      className="px-4 py-2 rounded-t-lg border"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h4 className="text-sm font-semibold text-gray-900">💬 最も議論が活発な解決案</h4>
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
                              {topData.age && (
                                <span className="bg-white px-2 py-1 rounded text-xs font-medium text-gray-700">
                                  {topData.age}歳
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <span className="text-xs bg-white px-2 py-1 rounded font-medium text-gray-700 border border-gray-300">
                          議論活発度: {Math.round(topData.impact_score * 100)}%
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
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default ChallengeAnalysisSummary;
