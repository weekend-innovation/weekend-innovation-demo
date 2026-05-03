/**
 * 課題分析結果サマリーコンポーネント
 * 期限切れ課題の分析結果を表示
 */
'use client';

import React, { useState, useMemo, useEffect } from 'react';
import type { ProposalListItem } from '../../types/proposal';
import ProposalClusterMap, {
  CLUSTER_COLORS,
  type ClusteringResult,
  type ClusterDataPoint,
} from './ProposalClusterMap';
import ProposalCard from '../proposals/ProposalCard';

interface CommonTheme {
  theme: string;
  frequency: number;
  percentage: number;
}

interface InnovativeSolution {
  proposal_id: number;
  innovation_score: number;
  outlier_score?: number;
  composite_score?: number;
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
  recommendations_source?: string;  // 'llm' | 'fallback' | ''
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
  onClusteringDataLoaded?: (data: ClusteringResult) => void;
  onAdoptChange?: (proposalId: number, isAdopted: boolean) => void | Promise<void>;
  /** 親で採用リスト・メモを管理する場合は渡す（分析と一覧で共有） */
  sharedAdoptionList?: Set<number>;
  sharedSetAdoptionList?: React.Dispatch<React.SetStateAction<Set<number>>>;
  sharedMemos?: Record<string, string>;
  sharedSetMemos?: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  /** 採用リストモーダルを親で表示する場合 */
  onOpenAddToAdoptionListModal?: (proposalId: number) => void;
  /** 採用リスト確定を親で処理する場合 */
  onConfirmAdoptionFromList?: () => void;
  confirmingAdoption?: boolean;
  /** 採用確定後はリスト操作・メモ編集を出さない */
  adoptionFinalized?: boolean;
}

const ChallengeAnalysisSummary: React.FC<ChallengeAnalysisSummaryProps> = ({
  analysis,
  proposals,
  challengeId,
  isLoading = false,
  onClusteringDataLoaded,
  sharedAdoptionList,
  sharedSetAdoptionList,
  sharedMemos,
  sharedSetMemos,
  onOpenAddToAdoptionListModal,
  adoptionFinalized = false,
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
  const [clusteringData, setClusteringData] = useState<ClusteringResult | null>(null);

  // 採用リスト・メモ（親から渡されていればそれを使用、否则は自前で localStorage）
  const STORAGE_PREFIX = `challenge_${challengeId}_`;
  const [internalConsiderationSet, setInternalConsiderationSet] = useState<Set<number>>(() => {
    if (typeof window === 'undefined') return new Set();
    try {
      const raw = localStorage.getItem(STORAGE_PREFIX + 'consideration');
      return raw ? new Set(JSON.parse(raw)) : new Set();
    } catch { return new Set(); }
  });
  const [internalMemos, setInternalMemos] = useState<Record<string, string>>(() => {
    if (typeof window === 'undefined') return {};
    try {
      const raw = localStorage.getItem(STORAGE_PREFIX + 'memos');
      return raw ? (JSON.parse(raw) as Record<string, string>) : {};
    } catch { return {}; }
  });
  const considerationSet = sharedAdoptionList ?? internalConsiderationSet;
  const setConsiderationSet = sharedSetAdoptionList ?? setInternalConsiderationSet;
  const memos = sharedMemos ?? internalMemos;
  const setMemos = sharedSetMemos ?? setInternalMemos;

  /** 解決案 ID 用（一覧・散布図の選択と一致） */
  const proposalMemoKey = (id: number) => String(Number(id));
  /** 「最も～」枠ごとに分離（同一提案が複数枠に出てもメモは独立） */
  const spotlightMemoKey = (slot: 'originality' | 'insightfulness' | 'impact', proposalId: number) =>
    `spot:${slot}:${Number(proposalId)}`;
  const readMemo = (key: string) => (memos[key] ?? '').trim();

  const [addToAdoptionListModalProposalId, setAddToAdoptionListModalProposalId] = useState<number | null>(null);
  const [memoEditModalKey, setMemoEditModalKey] = useState<string | null>(null);
  const [memoEditModalInput, setMemoEditModalInput] = useState('');

  useEffect(() => {
    if (sharedAdoptionList != null) return;
    try {
      localStorage.setItem(STORAGE_PREFIX + 'consideration', JSON.stringify([...internalConsiderationSet]));
    } catch {}
  }, [internalConsiderationSet, STORAGE_PREFIX, sharedAdoptionList]);
  useEffect(() => {
    if (sharedMemos != null) return;
    try {
      localStorage.setItem(STORAGE_PREFIX + 'memos', JSON.stringify(internalMemos));
    } catch {}
  }, [internalMemos, STORAGE_PREFIX, sharedMemos]);

  const addToAdoptionList = (proposalId: number) => {
    if (onOpenAddToAdoptionListModal) {
      onOpenAddToAdoptionListModal(proposalId);
      return;
    }
    setAddToAdoptionListModalProposalId(Number(proposalId));
  };
  const confirmAddToAdoptionList = () => {
    if (addToAdoptionListModalProposalId == null) return;
    setConsiderationSet((prev) => new Set(prev).add(addToAdoptionListModalProposalId));
    setAddToAdoptionListModalProposalId(null);
  };
  const openMemoByKey = (storageKey: string) => {
    setMemoEditModalKey(storageKey);
    setMemoEditModalInput(memos[storageKey] ?? '');
  };
  const closeMemoModal = () => {
    setMemoEditModalKey(null);
    setMemoEditModalInput('');
  };
  const confirmMemoModalSave = () => {
    if (memoEditModalKey == null) return;
    setMemos((prev) => ({ ...prev, [memoEditModalKey]: memoEditModalInput }));
    closeMemoModal();
  };
  const removeFromAdoptionList = (proposalId: number) => {
    setConsiderationSet((prev) => {
      const next = new Set(prev);
      next.delete(proposalId);
      return next;
    });
  };
  
  // 選択された解決案の詳細
  const selectedProposal = selectedProposalId 
    ? proposals.find(p => p.id === selectedProposalId) 
    : null;
  
  // 提案IDからクラスタ情報を取得する関数
  const getProposalCluster = (proposalId: number): number => {
    if (!clusteringData || !clusteringData.coordinates) return 0;
    const coordinate = clusteringData.coordinates.find(
      (c: ClusterDataPoint) => c.proposal_id === proposalId
    );
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
  
  // 総括テキスト（課題＋解決案に基づくアドバイス。バックエンドで生成）
  const summaryText = useMemo(() => {
    if (!analysis || analysis.status !== 'completed') return '';
    return (analysis.recommendations || '').trim();
  }, [analysis]);

  // クラスタ色から境界線の色を生成する関数
  const getClusterBorderColor = (cluster: number): string => {
    const baseColor = CLUSTER_COLORS[cluster % CLUSTER_COLORS.length];
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

  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500 space-y-2">
          <p>分析結果がありません。</p>
          <p className="text-sm text-gray-600">
            上部のスイッチで「解決案一覧」に切り替えると、解決案と採用リストを利用できます。
          </p>
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

        {/* 選択された解決案の詳細表示（マップとまとめの間に表示） */}
        {selectedProposal && (() => {
          const selCluster = getProposalCluster(selectedProposal.id);
          const selClusterInfo = clusteringData?.cluster_info?.find((c: { cluster_id: number }) => c.cluster_id === selCluster);
          const clusterSize = selClusterInfo?.size ?? 0;
          const nearbyCount = Math.max(0, clusterSize - 1);
          const trendTheme = selClusterInfo?.theme ?? '';
          const mainPointsSummary = selClusterInfo?.main_points_summary ?? '';
          return (
          <div className="border-2 border-blue-500 rounded-lg animate-pulse-once">
            <div className="bg-gray-100 px-4 py-2 rounded-t-lg flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900">選択中の解決案</h3>
              <button type="button" onClick={() => setSelectedProposalId(null)} className="cursor-pointer text-gray-700 hover:text-gray-900 text-sm font-medium">✕ 閉じる</button>
            </div>
            {clusteringData && clusterSize > 0 && (
              <div className="px-4 py-3 bg-blue-50 border-b border-blue-100 text-sm text-gray-700 space-y-2">
                <p><span className="font-medium">この案に近い意見：</span>{nearbyCount}件</p>
                {trendTheme && <p><span className="font-medium">類似意見の傾向：</span>{trendTheme}</p>}
                {mainPointsSummary && <p><span className="font-medium">主要な論点：</span>{mainPointsSummary}</p>}
              </div>
            )}
            <div className="p-2 flex gap-3 items-start">
              {!adoptionFinalized && (
              <div className="flex-shrink-0 pt-2 flex flex-col gap-2 w-[6rem]">
                {considerationSet.has(selectedProposal.id) ? (
                  <button type="button" onClick={() => removeFromAdoptionList(selectedProposal.id)} className="w-full px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 cursor-pointer">
                    外す
                  </button>
                ) : (
                  <button type="button" onClick={() => addToAdoptionList(selectedProposal.id)} className="w-full px-3 py-1.5 rounded-lg text-sm font-medium bg-green-600 text-white hover:bg-green-700 transition-colors cursor-pointer">
                    採用リスト
                  </button>
                )}
                <button type="button" onClick={() => openMemoByKey(proposalMemoKey(selectedProposal.id))} className={`w-full px-3 py-1.5 rounded-lg text-sm font-medium border cursor-pointer ${readMemo(proposalMemoKey(selectedProposal.id)) ? 'border-green-500 bg-green-50 text-green-800' : 'border-gray-300 bg-white hover:bg-gray-50 text-gray-700'}`}>
                  メモ{readMemo(proposalMemoKey(selectedProposal.id)) ? ' ✓' : ''}
                </button>
              </div>
              )}
              <div className="flex-1 min-w-0 space-y-2">
                <ProposalCard
                key={selectedProposal.id}
                proposal={{
                  ...selectedProposal,
                  nationality: selectedProposalAttributes?.nationality ?? selectedProposal.nationality,
                  gender: selectedProposalAttributes?.gender ?? selectedProposal.gender,
                  age: selectedProposalAttributes?.age ?? selectedProposal.age,
                }}
                showActions={false}
                showStatus={false}
                showComments={true}
                readOnlyComments={true}
                showChallengeInfo={false}
                useServerDataOnly={true}
                showUserAttributes={!!(selectedProposalAttributes?.is_selected && (selectedProposalAttributes?.nationality || selectedProposalAttributes?.gender || selectedProposalAttributes?.age != null))}
              />
              </div>
            </div>
          </div>
          );
        })()}

        {/* まとめ（合意/独創・多数派vs少数派・クラスタ比較を整理して表示） */}
        {clusteringData && (clusteringData.balance_summary || clusteringData.majority_minority_summary || (clusteringData.cluster_info && clusteringData.cluster_info.length > 0) || ((clusteringData.cluster_comparison?.similar_points?.length ?? 0) > 0 || (clusteringData.cluster_comparison?.different_points?.length ?? 0) > 0) || ((clusteringData.coordinates?.length ?? 0) > 0 && (clusteringData.cluster_centroids?.length ?? 0) > 0)) && (
          <div className="p-5 bg-gray-50 border border-gray-200 rounded-lg">
            <h4 className="text-base font-semibold text-gray-900 mb-4">📖 まとめ</h4>
            <p className="text-sm text-gray-600 mb-4">散布図の読み方と、クラスタごとの傾向をまとめています。</p>
            <div className="space-y-5 text-sm">
              {clusteringData.balance_summary && (
                <section className="p-3 bg-white border border-gray-200 rounded-md">
                  <h5 className="font-semibold text-amber-900 mb-2">1. 合意と独創性のバランス</h5>
                  <p className="text-amber-800 leading-relaxed">{clusteringData.balance_summary}</p>
                </section>
              )}
              {/* 合意・独創の具体例（1. の直下に配置） */}
              {(clusteringData?.coordinates?.length ?? 0) > 0 && (clusteringData?.cluster_centroids?.length ?? 0) > 0 && (() => {
                const coords = clusteringData.coordinates as { x: number; y: number; proposal_id: number; cluster: number }[];
                const centroids = clusteringData.cluster_centroids as { cluster_id: number; x: number; y: number }[];
                const getCentroid = (cluster: number) => centroids.find(c => c.cluster_id === cluster);
                const distances = coords.map(p => {
                  const cent = getCentroid(p.cluster);
                  if (!cent) return { proposal_id: p.proposal_id, dist: Infinity };
                  return { proposal_id: p.proposal_id, dist: Math.hypot(p.x - cent.x, p.y - cent.y) };
                });
                const closest = distances.length > 0 ? distances.reduce((a, b) => a.dist <= b.dist ? a : b) : null;
                const agreementProposalId = closest?.proposal_id ?? null;
                const originalProposalId = clusteringData?.most_original_proposal_id ?? analysis?.top_proposals?.originality?.proposal_id ?? null;
                const agreementProposal = agreementProposalId != null ? proposals.find(p => p.id === agreementProposalId) : null;
                const originalProposal = originalProposalId != null ? proposals.find(p => p.id === originalProposalId) : null;
                const quoteLen = 80;
                const quote = (s: string | undefined) => (s || '').trim().slice(0, quoteLen) + ((s || '').trim().length > quoteLen ? '…' : '');
                if (!agreementProposal && !originalProposal) return null;
                const agreementCluster = agreementProposal ? getProposalCluster(agreementProposal.id) : 0;
                const originalCluster = originalProposal ? getProposalCluster(originalProposal.id) : 0;
                const agreementBg = getClusterLightColor(agreementCluster);
                const agreementBorder = getClusterBorderColor(agreementCluster);
                const originalBg = getClusterLightColor(originalCluster);
                const originalBorder = getClusterBorderColor(originalCluster);
                return (
                  <section className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <h5 className="text-sm font-semibold text-gray-900 mb-3">📌 合意と独創の具体例</h5>
                    <p className="text-xs text-gray-600 mb-3">マップ上での「合意に近い」「独創的」のイメージを、代表的な解決案の結論で示しています。</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {agreementProposal && (
                        <div
                          className="rounded-lg border border-gray-200 overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
                          onClick={() => { setSelectedProposalId(agreementProposal.id === selectedProposalId ? null : agreementProposal.id); setSelectedProposalAttributes(null); }}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => { if (e.key === 'Enter') { setSelectedProposalId(agreementProposal.id === selectedProposalId ? null : agreementProposal.id); setSelectedProposalAttributes(null); } }}
                        >
                          <div className="px-3 py-2 border-b" style={{ backgroundColor: agreementBg, borderColor: agreementBorder }}>
                            <p className="text-xs font-medium text-gray-800">合意に近い例</p>
                          </div>
                          <div className="p-3">
                            <div className="bg-pink-50 rounded-lg p-3">
                              <p className="text-sm text-gray-800 leading-relaxed">{quote(agreementProposal.conclusion)}</p>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">クリックで詳細を表示</p>
                          </div>
                        </div>
                      )}
                      {originalProposal && (
                        <div
                          className="rounded-lg border border-gray-200 overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
                          onClick={() => { setSelectedProposalId(originalProposal.id === selectedProposalId ? null : originalProposal.id); setSelectedProposalAttributes(null); }}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => { if (e.key === 'Enter') { setSelectedProposalId(originalProposal.id === selectedProposalId ? null : originalProposal.id); setSelectedProposalAttributes(null); } }}
                        >
                          <div className="px-3 py-2 border-b" style={{ backgroundColor: originalBg, borderColor: originalBorder }}>
                            <p className="text-xs font-medium text-gray-800">独創的な例</p>
                          </div>
                          <div className="p-3">
                            <div className="bg-pink-50 rounded-lg p-3">
                              <p className="text-sm text-gray-800 leading-relaxed">{quote(originalProposal.conclusion)}</p>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">クリックで詳細を表示</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </section>
                );
              })()}
              {clusteringData.majority_minority_summary && (
                <section className="p-3 bg-white border border-gray-200 rounded-md">
                  <h5 className="font-semibold text-slate-900 mb-2">2. 多数派 vs 少数派</h5>
                  <p className="text-slate-700 mb-3 leading-relaxed">{clusteringData.majority_minority_summary}</p>
                  {clusteringData.cluster_info && clusteringData.cluster_info.length >= 2 && (() => {
                    const sorted = [...(clusteringData.cluster_info as { size: number; theme: string }[])].sort((a, b) => b.size - a.size);
                    const sizes = sorted.map(c => c.size);
                    const maxSize = Math.max(...sizes);
                    const minSize = Math.min(...sizes);
                    const hasMajorityMinority = maxSize > minSize;
                    return (
                      <table className="w-full text-sm border border-slate-300 rounded overflow-hidden">
                        <thead>
                          <tr className="bg-slate-200">
                            <th className="text-center py-2 px-3 font-medium text-slate-800">区分</th>
                            <th className="text-center py-2 px-3 font-medium text-slate-800">件数</th>
                            <th className="text-center py-2 px-3 font-medium text-slate-800">傾向</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sorted.map((c, i) => {
                            let label: string;
                            if (hasMajorityMinority) {
                              if (c.size === maxSize) label = '多数派';
                              else if (c.size === minSize) label = '少数派';
                              else label = 'その他';
                            } else {
                              label = `グループ${i + 1}`;
                            }
                            return (
                              <tr key={i} className={i === 0 ? 'bg-slate-100' : 'bg-white'}>
                                <td className="py-2 px-3 text-slate-700 text-center">{label}</td>
                                <td className="py-2 px-3 text-slate-700 text-center">{c.size}件</td>
                                <td className="py-2 px-3 text-slate-700 text-center">{c.theme || '—'}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    );
                  })()}
                </section>
              )}
              {clusteringData.cluster_info && clusteringData.cluster_info.length > 0 && (
                <section className="p-3 bg-white border border-gray-200 rounded-md">
                  <h5 className="font-semibold text-emerald-900 mb-2">3. 懸念と参考になる解決案</h5>
                  <p className="text-gray-600 text-xs mb-3">
                    各グループの懸念点と、その懸念を防ぐために参考にできる他グループの解決案を示しています。採用判断の際の補足としてご利用ください。
                  </p>
                  <div className="space-y-4">
                    {(clusteringData.cluster_info as { cluster_id: number; theme: string; size: number; concern?: string; recommended_proposal_ids?: number[] }[]).map((c) => {
                      const concern = c.concern ?? '特になし';
                      const recIds = c.recommended_proposal_ids ?? [];
                      return (
                        <div key={c.cluster_id} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="flex items-center gap-2 mb-2">
                            <div
                              className="w-3 h-3 rounded-full flex-shrink-0"
                              style={{ backgroundColor: CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length] }}
                            />
                            <span className="font-medium text-gray-900">{c.theme || `グループ${c.cluster_id + 1}`}</span>
                            <span className="text-xs text-gray-500">（{c.size}件）</span>
                          </div>
                          <p className="text-sm text-amber-800 mb-2">
                            <span className="font-medium text-amber-900">懸念：</span>{concern}
                          </p>
                          {recIds.length > 0 && (
                            <ul className="space-y-1">
                              {recIds.map((pid) => {
                                const p = proposals.find(pr => pr.id === pid);
                                if (!p) return null;
                                const cluster = getProposalCluster(pid);
                                const recBg = getClusterLightColor(cluster);
                                const recBorder = getClusterBorderColor(cluster);
                                const conclusionShort = (p.conclusion || '').trim().slice(0, 60) + ((p.conclusion || '').trim().length > 60 ? '…' : '');
                                return (
                                  <li key={pid}>
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setSelectedProposalId(pid === selectedProposalId ? null : pid);
                                        setSelectedProposalAttributes(null);
                                      }}
                                      className="w-full rounded border border-gray-200 overflow-hidden text-left cursor-pointer hover:opacity-90 transition-opacity"
                                    >
                                      <div className="px-2 py-1.5 border-b" style={{ backgroundColor: recBg, borderColor: recBorder }}>
                                        <p className="text-xs font-medium text-gray-800">参考になる解決案</p>
                                      </div>
                                      <div className="p-2">
                                        <div className="bg-pink-50 rounded-lg p-3">
                                          <p className="text-sm text-gray-800">{conclusionShort}</p>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">クリックで詳細を表示</p>
                                      </div>
                                    </button>
                                  </li>
                                );
                              })}
                            </ul>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}
            </div>
          </div>
        )}

        {/* 分析サマリー（散布図の下に「最も～」に選ばれた三つの解決案を表示） */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📊 分析サマリー
          </h3>

          {/* 最も独創的・最も支持・最も議論活発の三つの解決案カード */}
          {analysis.top_proposals && (
            <div className="space-y-6 mb-6">
              {/* 最も独創的な解決案 */}
              {(() => {
                const proposalId = clusteringData?.most_original_proposal_id ?? analysis.top_proposals?.originality?.proposal_id;
                const innovationScore = clusteringData?.most_original_innovation_score ?? analysis.top_proposals?.originality?.innovation_score;
                if (proposalId == null) return null;
                const coord = clusteringData?.coordinates?.find((c: { proposal_id: number }) => c.proposal_id === proposalId);
                const proposal = proposals.find(p => p.id === proposalId);
                if (!proposal) return null;
                const cluster = getProposalCluster(proposalId);
                const bgColor = getClusterLightColor(cluster);
                const borderColor = getClusterBorderColor(cluster);
                const isSelected = coord?.is_selected ?? analysis.top_proposals?.originality?.is_selected;
                const nationality = coord?.nationality ?? analysis.top_proposals?.originality?.nationality;
                const gender = coord?.gender ?? analysis.top_proposals?.originality?.gender;
                const age = coord?.age ?? analysis.top_proposals?.originality?.age;
                const attrs = { nationality, gender, age, is_selected: isSelected };
                const origMemoKey = spotlightMemoKey('originality', proposalId);
                return (
                  <div key={`spotlight-originality-${proposalId}`}>
                    <div
                      className="px-4 py-2 rounded-t-lg border cursor-pointer hover:opacity-90 transition-opacity"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                      onClick={() => {
                        setSelectedProposalId(proposalId === selectedProposalId ? null : proposalId);
                        setSelectedProposalAttributes(attrs);
                      }}
                      title="クリックで散布図の該当点を表示"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex-1 flex justify-center min-w-0 cursor-pointer">
                          <h4 className="text-base font-semibold text-gray-900"><span className="mr-2">⭐</span>最も独創的な解決案</h4>
                        </div>
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          {innovationScore != null && (
                            <span className="text-xs bg-white px-2 py-1 rounded font-medium text-gray-700 border border-gray-300">
                              革新性: {Math.round(innovationScore * 100)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div
                      className="border border-t-0 rounded-b-lg p-2 flex gap-3 items-start"
                      style={{ borderColor: borderColor }}
                    >
                      {!adoptionFinalized && (
                      <div className="flex-shrink-0 pt-2 flex flex-col gap-2 w-[6rem]">
                        {considerationSet.has(proposalId) ? (
                          <button type="button" onClick={() => removeFromAdoptionList(proposalId)} className="w-full px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 cursor-pointer">
                            外す
                          </button>
                        ) : (
                          <button type="button" onClick={() => addToAdoptionList(proposalId)} className="w-full px-3 py-1.5 rounded-lg text-sm font-medium bg-green-600 text-white hover:bg-green-700 transition-colors cursor-pointer">
                            採用リスト
                          </button>
                        )}
                        <button type="button" onClick={() => openMemoByKey(origMemoKey)} className={`w-full px-3 py-1.5 rounded-lg text-sm font-medium border cursor-pointer ${readMemo(origMemoKey) ? 'border-green-500 bg-green-50 text-green-800' : 'border-gray-300 bg-white hover:bg-gray-50 text-gray-700'}`}>
                          メモ{readMemo(origMemoKey) ? ' ✓' : ''}
                        </button>
                      </div>
                      )}
                      <div className="flex-1 min-w-0 space-y-2">
                        <ProposalCard
                          proposal={{ ...proposal, nationality: attrs.nationality ?? proposal.nationality, gender: attrs.gender ?? proposal.gender, age: attrs.age ?? proposal.age }}
                          showActions={false}
                          showStatus={false}
                          showComments={true}
                          readOnlyComments={true}
                          showChallengeInfo={false}
                          useServerDataOnly={true}
                          showUserAttributes={isSelected && !!(nationality || gender || age != null)}
                        />
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* 最も支持されている解決案 */}
              {analysis.top_proposals.insightfulness && (() => {
                const proposal = proposals.find(p => p.id === analysis.top_proposals?.insightfulness?.proposal_id);
                const topData = analysis.top_proposals.insightfulness;
                const cluster = getProposalCluster(topData.proposal_id);
                const bgColor = getClusterLightColor(cluster);
                const borderColor = getClusterBorderColor(cluster);
                const attrs = { nationality: topData.nationality, gender: topData.gender, age: topData.age, is_selected: topData.is_selected };
                const insMemoKey = spotlightMemoKey('insightfulness', Number(topData.proposal_id));
                return proposal && (
                  <div key={`spotlight-insightfulness-${topData.proposal_id}`}>
                    <div
                      className="px-4 py-2 rounded-t-lg border cursor-pointer hover:opacity-90 transition-opacity"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                      onClick={() => {
                        setSelectedProposalId(topData.proposal_id === selectedProposalId ? null : topData.proposal_id);
                        setSelectedProposalAttributes(attrs);
                      }}
                      title="クリックで散布図の該当点を表示"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex-1 flex justify-center min-w-0 cursor-pointer">
                          <h4 className="text-base font-semibold text-gray-900"><span className="mr-2">💡</span>最も支持されている解決案</h4>
                        </div>
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          <span className="text-xs bg-white px-2 py-1 rounded font-medium text-gray-700 border border-gray-300">
                            支持率: {Math.round(topData.insightfulness_score * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <div
                      className="border border-t-0 rounded-b-lg p-2 flex gap-3 items-start"
                      style={{ borderColor: borderColor }}
                    >
                      {!adoptionFinalized && (
                      <div className="flex-shrink-0 pt-2 flex flex-col gap-2 w-[6rem]">
                        {considerationSet.has(topData.proposal_id) ? (
                          <button type="button" onClick={() => removeFromAdoptionList(topData.proposal_id)} className="w-full px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 cursor-pointer">
                            外す
                          </button>
                        ) : (
                          <button type="button" onClick={() => addToAdoptionList(topData.proposal_id)} className="w-full px-3 py-1.5 rounded-lg text-sm font-medium bg-green-600 text-white hover:bg-green-700 transition-colors cursor-pointer">
                            採用リスト
                          </button>
                        )}
                        <button type="button" onClick={() => openMemoByKey(insMemoKey)} className={`w-full px-3 py-1.5 rounded-lg text-sm font-medium border cursor-pointer ${readMemo(insMemoKey) ? 'border-green-500 bg-green-50 text-green-800' : 'border-gray-300 bg-white hover:bg-gray-50 text-gray-700'}`}>
                          メモ{readMemo(insMemoKey) ? ' ✓' : ''}
                        </button>
                      </div>
                      )}
                      <div className="flex-1 min-w-0 space-y-2">
                        <ProposalCard
                          proposal={{ ...proposal, nationality: topData.nationality ?? proposal.nationality, gender: topData.gender ?? proposal.gender, age: topData.age ?? proposal.age }}
                          showActions={false}
                          showStatus={false}
                          showComments={true}
                          readOnlyComments={true}
                          showChallengeInfo={false}
                          useServerDataOnly={true}
                          showUserAttributes={!!(topData.is_selected && (topData.nationality || topData.gender || topData.age != null))}
                        />
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* 最も議論が活発な解決案 */}
              {analysis.top_proposals.impact && (() => {
                const proposal = proposals.find(p => p.id === analysis.top_proposals?.impact?.proposal_id);
                const topData = analysis.top_proposals.impact;
                const cluster = getProposalCluster(topData.proposal_id);
                const bgColor = getClusterLightColor(cluster);
                const borderColor = getClusterBorderColor(cluster);
                const attrs = { nationality: topData.nationality, gender: topData.gender, age: topData.age, is_selected: topData.is_selected };
                const impMemoKey = spotlightMemoKey('impact', Number(topData.proposal_id));
                return proposal && (
                  <div key={`spotlight-impact-${topData.proposal_id}`}>
                    <div
                      className="px-4 py-2 rounded-t-lg border cursor-pointer hover:opacity-90 transition-opacity"
                      style={{ backgroundColor: bgColor, borderColor: borderColor }}
                      onClick={() => {
                        setSelectedProposalId(topData.proposal_id === selectedProposalId ? null : topData.proposal_id);
                        setSelectedProposalAttributes(attrs);
                      }}
                      title="クリックで散布図の該当点を表示"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex-1 flex justify-center min-w-0 cursor-pointer">
                          <h4 className="text-base font-semibold text-gray-900"><span className="mr-2">💬</span>最も議論が活発な解決案</h4>
                        </div>
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          <span className="text-xs bg-white px-2 py-1 rounded font-medium text-gray-700 border border-gray-300">
                            影響度: {Math.round(topData.impact_score * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <div
                      className="border border-t-0 rounded-b-lg p-2 flex gap-3 items-start"
                      style={{ borderColor: borderColor }}
                    >
                      {!adoptionFinalized && (
                      <div className="flex-shrink-0 pt-2 flex flex-col gap-2 w-[6rem]">
                        {considerationSet.has(topData.proposal_id) ? (
                          <button type="button" onClick={() => removeFromAdoptionList(topData.proposal_id)} className="w-full px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 cursor-pointer">
                            外す
                          </button>
                        ) : (
                          <button type="button" onClick={() => addToAdoptionList(topData.proposal_id)} className="w-full px-3 py-1.5 rounded-lg text-sm font-medium bg-green-600 text-white hover:bg-green-700 transition-colors cursor-pointer">
                            採用リスト
                          </button>
                        )}
                        <button type="button" onClick={() => openMemoByKey(impMemoKey)} className={`w-full px-3 py-1.5 rounded-lg text-sm font-medium border cursor-pointer ${readMemo(impMemoKey) ? 'border-green-500 bg-green-50 text-green-800' : 'border-gray-300 bg-white hover:bg-gray-50 text-gray-700'}`}>
                          メモ{readMemo(impMemoKey) ? ' ✓' : ''}
                        </button>
                      </div>
                      )}
                      <div className="flex-1 min-w-0 space-y-2">
                        <ProposalCard
                          proposal={{ ...proposal, nationality: topData.nationality ?? proposal.nationality, gender: topData.gender ?? proposal.gender, age: topData.age ?? proposal.age }}
                          showActions={false}
                          showStatus={false}
                          showComments={true}
                          readOnlyComments={true}
                          showChallengeInfo={false}
                          useServerDataOnly={true}
                          showUserAttributes={!!(topData.is_selected && (topData.nationality || topData.gender || topData.age != null))}
                        />
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* 採用リストはページ最下部に統合表示（トグルに依存しない） */}

          {/* 総括：課題投稿者（企業・自治体）向けの有益な示唆 */}
          {summaryText && (
            <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-gray-900">📋 総括</h4>
                {analysis.recommendations_source && (
                  <span className="text-xs text-gray-500">
                    {analysis.recommendations_source === 'llm'
                      ? '✨ AI（Gemini）生成'
                      : '📋 テンプレート'}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">{summaryText}</p>
            </div>
          )}
        </div>

      </div>

      {memoEditModalKey != null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4" onClick={() => closeMemoModal()}>
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4 border border-gray-200" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">メモ</h3>
            <p className="text-sm text-gray-600 mb-3">
              採用判断のときの備忘録として入力できます。一覧の「メモ ✓」からいつでも開けます。
            </p>
            <textarea
              value={memoEditModalInput}
              onChange={(e) => setMemoEditModalInput(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-3 min-h-[100px] mb-4 focus:outline-none focus:ring-2 focus:ring-green-500/40"
              placeholder=""
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <button type="button" className="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg" onClick={() => closeMemoModal()}>
                キャンセル
              </button>
              <button type="button" onClick={() => confirmMemoModalSave()} className="cursor-pointer px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg">
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 採用リストモーダル（親がモーダルを表示する場合は表示しない） */}
      {!onOpenAddToAdoptionListModal && addToAdoptionListModalProposalId != null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4" onClick={() => { setAddToAdoptionListModalProposalId(null); }}>
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4 border border-gray-200" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">採用リストに追加</h3>
            <p className="text-sm text-gray-600 mb-4">この解決案を採用リストに追加します。メモは「メモ」ボタンから入力できます。</p>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => { setAddToAdoptionListModalProposalId(null); }} className="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg">
                キャンセル
              </button>
              <button type="button" onClick={confirmAddToAdoptionList} className="cursor-pointer px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg">
                追加
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChallengeAnalysisSummary;
