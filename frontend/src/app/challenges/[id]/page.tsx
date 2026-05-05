/**
 * 課題詳細ページ
 * 課題の詳細情報を表示
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import type { Challenge } from '../../../types/challenge';
import type { ProposalListItem } from '../../../types/proposal';
import { getChallenge, deleteChallenge, finalizeAdoption } from '../../../lib/challengeAPI';
import { getProposalsByChallenge, getUserProposalForChallenge, setProposalAdopted } from '../../../lib/proposalAPI';
import { getChallengeAnalysis, getMyProposalInsight, type ChallengeAnalysisData, type ProposalInsight } from '../../../lib/analyticsAPI';
import { useAuth } from '../../../contexts/AuthContext';
import { isProposerExpiredOrFailed, isAllPhasesCompleted, canProposerViewResults } from '../../../lib/challengeSortUtils';
import ProposalCard from '../../../components/proposals/ProposalCard';
import ChallengeAnalysisSummary from '../../../components/analytics/ChallengeAnalysisSummary';
import type { ClusteringResult } from '../../../components/analytics/ProposalClusterMap';
import AnalysisToggleSwitch from '../../../components/analytics/AnalysisToggleSwitch';
import ProposerAnalysisSummary from '../../../components/analytics/ProposerAnalysisSummary';
import { DemoRewardAmountPlaceholder } from '../../../components/common/DemoRewardDisclaimer';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

const ChallengeDetailPage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);
  const [userProposal, setUserProposal] = useState<ProposalListItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 分析機能用のstate
  const [analysis, setAnalysis] = useState<ChallengeAnalysisData | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(true); // デフォルトで分析結果を表示
  const [analysisLoading, setAnalysisLoading] = useState(false);
  
  // 提案者向け分析用のstate
  const [myInsight, setMyInsight] = useState<ProposalInsight | null>(null);
  
  // クラスタリングデータ用のstate
  const [clusteringData, setClusteringData] = useState<ClusteringResult | null>(null);

  // 解決案一覧のページネーション（25件/ページ）
  const [solutionListPage, setSolutionListPage] = useState(1);
  const SOLUTION_LIST_PAGE_SIZE = 25;

  // 採用リスト・メモ（分析と一覧で共有、localStorage に保存）
  const challengeIdStr = params.id as string;
  const STORAGE_PREFIX = `challenge_${challengeIdStr}_`;
  const [adoptionList, setAdoptionList] = useState<Set<number>>(() => {
    if (typeof window === 'undefined') return new Set();
    try {
      const raw = localStorage.getItem(STORAGE_PREFIX + 'consideration');
      return raw ? new Set(JSON.parse(raw)) : new Set();
    } catch { return new Set(); }
  });
  const [adoptionListMemos, setAdoptionListMemos] = useState<Record<string, string>>(() => {
    if (typeof window === 'undefined') return {};
    try {
      const raw = localStorage.getItem(STORAGE_PREFIX + 'memos');
      return raw ? (JSON.parse(raw) as Record<string, string>) : {};
    } catch { return {}; }
  });
  const [addToAdoptionListModalId, setAddToAdoptionListModalId] = useState<number | null>(null);
  const [memoEditModalProposalId, setMemoEditModalProposalId] = useState<number | null>(null);
  const [memoEditModalInput, setMemoEditModalInput] = useState('');
  const [confirmingAdoption, setConfirmingAdoption] = useState(false);
  const [adoptionFinalizeModalOpen, setAdoptionFinalizeModalOpen] = useState(false);
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_PREFIX + 'consideration', JSON.stringify([...adoptionList]));
    } catch {}
  }, [adoptionList, STORAGE_PREFIX]);
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_PREFIX + 'memos', JSON.stringify(adoptionListMemos));
    } catch {}
  }, [adoptionListMemos, STORAGE_PREFIX]);

  const confirmAddToAdoptionList = () => {
    if (addToAdoptionListModalId == null) return;
    setAdoptionList((prev) => new Set([...prev, addToAdoptionListModalId]));
    setAddToAdoptionListModalId(null);
  };
  const saveMemoFromModal = () => {
    if (memoEditModalProposalId == null) return;
    const key = String(memoEditModalProposalId);
    setAdoptionListMemos((prev) => ({ ...prev, [key]: memoEditModalInput }));
    setMemoEditModalProposalId(null);
    setMemoEditModalInput('');
  };
  const openAdoptionFinalizeConfirm = () => {
    if (adoptionList.size === 0) return;
    setAdoptionFinalizeModalOpen(true);
  };

  const reloadProposalsForChallenge = async () => {
    const cid = parseInt(challengeId, 10);
    const proposalsData = await getProposalsByChallenge(cid);
    let allProposals = proposalsData.results;
    let nextUrl = proposalsData.next;
    while (nextUrl) {
      const token = localStorage.getItem('access_token');
      const response = await fetch(nextUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      const nextData = await response.json();
      allProposals = [...allProposals, ...nextData.results];
      nextUrl = nextData.next;
    }
    setProposals(allProposals);
  };

  const executeFinalizeAdoption = async () => {
    if (adoptionList.size === 0) return;
    setConfirmingAdoption(true);
    try {
      const updated = await finalizeAdoption(parseInt(challengeId, 10), [...adoptionList]);
      setChallenge(updated);
      await reloadProposalsForChallenge();
      setAdoptionList(new Set());
      setAdoptionFinalizeModalOpen(false);
      alert('採用を確定しました。この操作は取り消せません。');
    } catch (e) {
      console.error('採用確定エラー:', e);
      alert(e instanceof Error ? e.message : '採用の確定に失敗しました。');
    } finally {
      setConfirmingAdoption(false);
    }
  };

  // 採用トグル（投稿者向け・分析・一覧の両方で使用）
  const handleAdoptToggle = async (proposalId: number, isAdopted: boolean) => {
    if (challenge?.status === 'completed') {
      alert('採用はすでに確定済みのため変更できません。');
      return;
    }
    try {
      await setProposalAdopted(proposalId, isAdopted);
      setProposals(prev => prev.map(p =>
        p.id === proposalId ? { ...p, is_adopted: isAdopted } : p
      ));
    } catch (e) {
      console.error('採用設定エラー:', e);
      alert('採用の設定に失敗しました。');
    }
  };

  const challengeId = params.id as string;

  // 投稿者向け分析データの取得
  const fetchAnalysisData = async () => {
    if (!challenge || (challenge.status !== 'closed' && challenge.status !== 'completed')) return;
    
    try {
      setAnalysisLoading(true);
      
      const analysisData = await getChallengeAnalysis(parseInt(challengeId));
      setAnalysis(analysisData);
    } catch (error) {
      console.error('分析データ取得エラー:', error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  // 提案者向け分析データの取得（提案＋評価完了した場合のみ）
  const fetchMyInsightData = async () => {
    if (
      !challenge ||
      (challenge.status !== 'closed' && challenge.status !== 'completed') ||
      !userProposal ||
      !challenge.has_completed_all_evaluations
    ) {
      return;
    }
    
    try {
      setAnalysisLoading(true);
      
      const analysisData = await getChallengeAnalysis(parseInt(challengeId));
      setAnalysis(analysisData);
      
      const insightData = await getMyProposalInsight(parseInt(challengeId), userProposal.id);
      setMyInsight(insightData);
      
      // クラスタリングデータの取得（提案者用）
      try {
        const clusteringResponse = await fetch(
          `${API_BASE_URL}/analytics/challenges/${challengeId}/clustering/`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );
        if (clusteringResponse.ok) {
          const clusteringResult = await clusteringResponse.json();
          setClusteringData(clusteringResult);
        }
      } catch {
        // クラスタリングデータの取得失敗は致命的ではないため、エラーを表示しない
      }
    } catch {
    } finally {
      setAnalysisLoading(false);
    }
  };

  // 課題詳細と解決案の取得
  const fetchChallengeData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 課題詳細の取得
      const challengeData = await getChallenge(parseInt(challengeId));
      setChallenge(challengeData);
      
      // 提案者の場合、解決案を取得
      if (user?.user_type === 'proposer' && isAuthenticated) {
        // ユーザーの提案状況を確認
        const userProposalData = await getUserProposalForChallenge(parseInt(challengeId));
        if (userProposalData) {
          // ProposalをProposalListItemに変換
          const proposalListItem: ProposalListItem = {
            id: userProposalData.id,
            conclusion: userProposalData.conclusion,
            reasoning: userProposalData.reasoning,
            challenge_id: userProposalData.challenge,
            challenge_title: userProposalData.challenge_info?.title || '',
            proposer_name: userProposalData.proposer_info?.username || '',
            anonymous_name_info: userProposalData.anonymous_name,
            is_anonymous: userProposalData.is_anonymous,
            status: userProposalData.status,
            is_adopted: userProposalData.is_adopted,
            rating: userProposalData.rating,
            rating_count: userProposalData.rating_count,
            created_at: userProposalData.created_at,
            updated_at: userProposalData.updated_at,
            unread_comment_count: userProposalData.unread_comment_count || 0,
            total_comment_count: userProposalData.total_comment_count || 0,
          };
          setUserProposal(proposalListItem);
        } else {
          setUserProposal(null);
        }
        
        // ユーザーが提案済みの場合のみ、他の提案も取得（全件取得）
        if (userProposalData) {
          const proposalsData = await getProposalsByChallenge(parseInt(challengeId));
          let allProposals = proposalsData.results;
          let nextUrl = proposalsData.next;
          
          // 次のページがある場合は全て取得
          while (nextUrl) {
            const token = localStorage.getItem('access_token');
            const response = await fetch(nextUrl, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            });
            const nextData = await response.json();
            allProposals = [...allProposals, ...nextData.results];
            nextUrl = nextData.next;
          }
          
          setProposals(allProposals);
        }
      }
      
      // 投稿者の場合は全ての解決案を取得（全件取得のため大きなページサイズを指定）
      if (user?.user_type === 'contributor' && isAuthenticated) {
        const proposalsData = await getProposalsByChallenge(parseInt(challengeId));
        // 全ての解決案を取得（ページネーション対応）
        let allProposals = proposalsData.results;
        let nextUrl = proposalsData.next;
        
        // 次のページがある場合は全て取得
        while (nextUrl) {
          const token = localStorage.getItem('access_token');
          const response = await fetch(nextUrl, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          const nextData = await response.json();
          allProposals = [...allProposals, ...nextData.results];
          nextUrl = nextData.next;
        }
        
        setProposals(allProposals);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (challengeId && isAuthenticated && user) {
      fetchChallengeData();
    } else if (!isAuthenticated) {
      setLoading(false);
    }
  }, [challengeId, isAuthenticated, user]); // eslint-disable-line react-hooks/exhaustive-deps

  // 分析データの取得（課題データ取得後）
  useEffect(() => {
    if (challenge && (challenge.status === 'closed' || challenge.status === 'completed')) {
      if (user?.user_type === 'contributor') {
        // 投稿者向け分析
        fetchAnalysisData();
      } else if (user?.user_type === 'proposer' && userProposal && challenge.has_completed_all_evaluations) {
        // 提案者向け分析（評価完了済みのみ）
        fetchMyInsightData();
      }
    }
  }, [challenge, userProposal]); // eslint-disable-line react-hooks/exhaustive-deps

  // 認証チェック（すべてのHooksの後に配置）
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              ログインが必要です
            </h2>
            <p className="text-yellow-700 mb-4">
              このページを閲覧するにはログインが必要です。
            </p>
            <Link
              href="/auth/login"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              ログイン
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 期限の表示形式
  const formatDeadline = (deadline: string) => {
    const date = new Date(deadline);
    // UTCの値をそのまま使用（日本時間への変換を避ける）
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    return `${year}年${month}月${day}日 ${hours}:${minutes}`;
  };

  const isExpired = (deadline: string) => {
    return new Date(deadline) < new Date();
  };

  // ローディング表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-600">読み込み中...</div>
          </div>
        </div>
      </div>
    );
  }

  // エラー表示
  if (error || !challenge) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-red-800 mb-2">
              エラーが発生しました
            </h2>
            <p className="text-red-700 mb-4">
              {error || '課題が見つかりません'}
            </p>
            <Link
              href="/challenges"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              課題一覧に戻る
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const challengeForProposer = { ...challenge, has_proposed: !!userProposal };
  const expiredOrFailed = user?.user_type === 'proposer' && isProposerExpiredOrFailed(challengeForProposer);
  const allPhasesDone = user?.user_type === 'proposer' && isAllPhasesCompleted(challengeForProposer);
  const adoptionFinalized = challenge.status === 'completed';
  const contributorPastDeadline =
    user?.user_type === 'contributor' &&
    (challenge.current_phase === 'closed' || isExpired(challenge.deadline));
  const contributorAdoptionPending = contributorPastDeadline && !adoptionFinalized;
  const canManageAdoptionList = contributorAdoptionPending;
  const proposerChallengeCompleted =
    user?.user_type === 'proposer' && adoptionFinalized;
  const proposerPendingAdoptionAfterParticipation =
    user?.user_type === 'proposer' &&
    !adoptionFinalized &&
    challenge.status === 'closed' &&
    canProposerViewResults(challengeForProposer);

  const phaseMain =
    challenge.phase_display || (isExpired(challenge.deadline) ? '満了' : '募集中');

  const phaseStatusVisual = (): {
    panel: string;
    caption: string;
    value: string;
    main: string;
  } => {
    /** 提案期間: 採用報酬（bg-green-50）よりわずかに濃くして区別 */
    if (challenge.current_phase === 'proposal') {
      return {
        panel: 'bg-green-100 border border-green-300',
        caption: 'text-green-700',
        value: 'font-bold text-green-900',
        main: phaseMain,
      };
    }
    if (challenge.current_phase === 'edit') {
      return {
        panel: 'bg-yellow-50',
        caption: 'text-yellow-600',
        value: 'font-bold text-yellow-900',
        main: phaseMain,
      };
    }
    if (challenge.current_phase === 'evaluation') {
      return {
        panel: 'bg-orange-50',
        caption: 'text-orange-600',
        value: 'font-bold text-orange-900',
        main: phaseMain,
      };
    }
    return {
      panel: 'bg-red-50',
      caption: 'text-red-600',
      value: 'font-bold text-red-900',
      main: phaseMain,
    };
  };

  const proposerStatusBox = (() => {
    if (proposerChallengeCompleted) {
      return {
        panel: 'bg-gray-100 border border-gray-400',
        caption: 'text-gray-500',
        value: 'font-semibold text-gray-600',
        main: '完了',
      };
    }
    if (proposerPendingAdoptionAfterParticipation) {
      return {
        panel: 'bg-amber-50 border border-amber-200',
        caption: 'text-amber-800',
        value: 'font-bold text-amber-900',
        main: '期間満了（採用未確定）',
      };
    }
    if (expiredOrFailed) {
      return {
        panel: 'bg-red-50',
        caption: 'text-red-600',
        value: 'font-bold text-red-900',
        main: '期限切れ',
      };
    }
    if (allPhasesDone) {
      return {
        panel: 'bg-teal-50',
        caption: 'text-teal-600',
        value: 'font-bold text-teal-900',
        main: '全フェーズ達成',
      };
    }
    return phaseStatusVisual();
  })();

  const statusBox =
    user?.user_type === 'contributor'
      ? adoptionFinalized
        ? {
            panel: 'bg-gray-100 border border-gray-400',
            caption: 'text-gray-500',
            value: 'font-semibold text-gray-600',
            main: '完了',
          }
        : contributorAdoptionPending
          ? {
              panel: 'bg-amber-50 border border-amber-200',
              caption: 'text-amber-800',
              value: 'font-bold text-amber-900',
              main: '期間満了（採用未確定）',
            }
          : phaseStatusVisual()
      : user?.user_type === 'proposer'
        ? proposerStatusBox
        : phaseStatusVisual();

  return (
    <div className="min-h-screen bg-gray-50 py-8 w-full">
      {/* パンくずリスト */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
        <nav className="flex items-center space-x-2 text-sm text-gray-500">
            <Link href="/dashboard" className="hover:text-gray-700">
              ホーム
            </Link>
          <span>/</span>
          <Link href="/challenges" className="hover:text-gray-700">
            課題一覧
          </Link>
          <span>/</span>
          <span className="text-gray-900 font-medium">課題詳細</span>
        </nav>
      </div>

      {/* メインコンテンツ（中央寄せ・固定幅） */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 課題カード・解決案エリアに青い線のような余白 */}
        <div className="max-w-4xl mx-auto px-8 sm:px-10">
        {/* 課題概要と内容（コンパクト） */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="mb-4">
            <div className="flex items-start justify-between mb-2">
              <h1 className="text-[1.3125rem] font-bold text-gray-900 flex-1 pr-4">
                {challenge.title}
              </h1>
              <div className="flex flex-col items-end gap-1 text-sm text-gray-600">
                <span>投稿者: {challenge.contributor_name || challenge.contributor_info?.username || '不明'}</span>
                <span>投稿日: {new Date(challenge.created_at).toLocaleDateString('ja-JP')}</span>
                {challenge.updated_at && challenge.updated_at !== challenge.created_at && (
                  <span className="text-xs text-gray-500">編集日時: {new Date(challenge.updated_at).toLocaleDateString('ja-JP')} {new Date(challenge.updated_at).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}</span>
                )}
              </div>
            </div>
          </div>

          {/* 報酬と期限（コンパクト・デモは金額非表示） */}
          <div className="space-y-4 mb-4">
            {/* 報酬情報（2列） */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <p className="text-sm text-blue-600 font-medium mb-1">提案報酬</p>
                <p className="text-lg font-bold text-blue-900">
                  <DemoRewardAmountPlaceholder className="text-lg font-bold text-blue-900" />
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-3 text-center">
                <p className="text-sm text-green-600 font-medium mb-1">採用報酬</p>
                <p className="text-lg font-bold text-green-900">
                  <DemoRewardAmountPlaceholder className="text-lg font-bold text-green-900" />
                </p>
              </div>
            </div>
            {/* 期限・状況 */}
            <div>
              <div className={`rounded-lg p-3 text-center ${statusBox.panel}`}>
                <p className={`text-sm font-medium mb-1 ${statusBox.caption}`}>期限・状況</p>
                <p className={`text-lg mb-1 ${statusBox.value}`}>{statusBox.main}</p>
                {/* 評価完了バッジ（全フェーズ達成時は表示しない） */}
                {challenge.has_completed_all_evaluations && !allPhasesDone && !expiredOrFailed && (
                  <div className="mt-2 pt-2 border-t border-purple-200">
                    <p className="text-sm font-bold text-purple-600">
                      ✓ 全評価完了
                    </p>
                  </div>
                )}
              </div>
              {/* 現在フェーズの期限（枠の下・右寄せ） */}
              {challenge.current_phase && challenge.current_phase !== 'closed' && (
                <div className="flex justify-end mt-2">
                  <div className="text-right text-sm text-gray-700">
                    {challenge.current_phase === 'proposal' && challenge.proposal_deadline && (
                      <>
                        <span className="font-medium">提案期限</span>
                        <span className="ml-1">{formatDeadline(challenge.proposal_deadline)}</span>
                      </>
                    )}
                    {challenge.current_phase === 'edit' && challenge.edit_deadline && (
                      <>
                        <span className="font-medium">編集期限</span>
                        <span className="ml-1">{formatDeadline(challenge.edit_deadline)}</span>
                      </>
                    )}
                    {challenge.current_phase === 'evaluation' && challenge.evaluation_deadline && (
                      <>
                        <span className="font-medium">評価期限</span>
                        <span className="ml-1">{formatDeadline(challenge.evaluation_deadline)}</span>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 進捗バー */}
          {challenge.current_phase && challenge.current_phase !== 'closed' && challenge.proposal_deadline && challenge.edit_deadline && challenge.evaluation_deadline && (
            <div className="border-t border-gray-200 pt-4 pb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">進捗状況</h3>
              <div className="relative mt-8">
                {/* 進捗バー本体 */}
                <div className="h-6 bg-gray-200 rounded overflow-hidden flex">
                  {(() => {
                    const start = new Date(challenge.created_at);
                    const proposalEnd = new Date(challenge.proposal_deadline);
                    const editEnd = new Date(challenge.edit_deadline);
                    const evaluationEnd = new Date(challenge.evaluation_deadline);
                    
                    const totalDuration = evaluationEnd.getTime() - start.getTime();
                    const proposalDuration = proposalEnd.getTime() - start.getTime();
                    const editDuration = editEnd.getTime() - proposalEnd.getTime();
                    const evaluationDuration = evaluationEnd.getTime() - editEnd.getTime();
                    
                    const proposalWidth = (proposalDuration / totalDuration) * 100;
                    const editWidth = (editDuration / totalDuration) * 100;
                    const evaluationWidth = (evaluationDuration / totalDuration) * 100;
                    
                    return (
                      <>
                        {/* 各フェーズの区間 */}
                        <div 
                          className={`flex items-center justify-center text-xs font-semibold border-r border-white ${
                            challenge.current_phase === 'proposal' ? 'bg-green-400 text-white' : 'bg-green-200 text-green-800'
                          }`}
                          style={{ width: `${proposalWidth}%` }}
                        >
                          提案
                        </div>
                        <div 
                          className={`flex items-center justify-center text-xs font-semibold border-r border-white ${
                            challenge.current_phase === 'edit' ? 'bg-yellow-400 text-white' : 'bg-yellow-200 text-yellow-800'
                          }`}
                          style={{ width: `${editWidth}%` }}
                        >
                          編集
                        </div>
                        <div 
                          className={`flex items-center justify-center text-xs font-semibold ${
                            challenge.current_phase === 'evaluation' ? 'bg-orange-400 text-white' : 'bg-orange-200 text-orange-800'
                          }`}
                          style={{ width: `${evaluationWidth}%` }}
                        >
                          評価
                        </div>
                      </>
                    );
                  })()}
                </div>
                
                {/* 進捗インジケーター（現在位置） */}
                {(() => {
                  const now = new Date();
                  const start = new Date(challenge.created_at);
                  const end = new Date(challenge.evaluation_deadline);
                  const totalDuration = end.getTime() - start.getTime();
                  const elapsed = now.getTime() - start.getTime();
                  const progress = Math.min(Math.max((elapsed / totalDuration) * 100, 0), 100);
                  
                  return (
                    <div 
                      className="absolute top-0 h-6 w-0.5 bg-gray-800"
                      style={{ left: `${progress}%`, transform: 'translateX(-50%)' }}
                    >
                      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-800 rounded-full -mt-1"></div>
                      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-800 rounded-full -mb-1"></div>
                    </div>
                  );
                })()}
              </div>
              
              {/* 各期限の詳細表示 */}
              <div className="grid grid-cols-3 gap-2 mt-3 text-xs text-gray-600">
                <div className="text-center">
                  <p className="font-semibold text-gray-700">提案期限</p>
                  <p>～{challenge.proposal_deadline && formatDeadline(challenge.proposal_deadline)}</p>
                </div>
                <div className="text-center">
                  <p className="font-semibold text-gray-700">編集期限</p>
                  <p>～{challenge.edit_deadline && formatDeadline(challenge.edit_deadline)}</p>
                </div>
                <div className="text-center">
                  <p className="font-semibold text-gray-700">評価期限</p>
                  <p>～{challenge.evaluation_deadline && formatDeadline(challenge.evaluation_deadline)}</p>
                </div>
              </div>
            </div>
          )}

          {/* 課題内容 */}
          <div className="border-t border-gray-200 pt-4">
            <h2 className="text-[1.1875rem] font-semibold text-gray-900 mb-3">課題内容</h2>
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap pl-4">
                {challenge.description}
              </p>
            </div>
          </div>

          {/* 投稿者のみ編集・削除（deadline 過ぎていれば編集不可） */}
          {user?.user_type === 'contributor' && (
            <div className="flex justify-end gap-4 pt-4 border-t border-gray-200 mt-4">
              {!isExpired(challenge.deadline) && (
                <Link
                  href={`/challenges/${challenge.id}/edit`}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 font-medium cursor-pointer"
                >
                  編集
                </Link>
              )}
              <button
                onClick={async () => {
                  if (confirm('この課題を削除しますか？\n\n削除すると、この課題に関連する全ての解決案も削除されます。この操作は取り消せません。')) {
                    try {
                      await deleteChallenge(challenge.id);
                      alert('課題を削除しました');
                      router.push('/challenges');
                    } catch (error) {
                      console.error('課題削除エラー:', error);
                      alert('課題の削除に失敗しました');
                    }
                  }
                }}
                className="px-6 py-3 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors duration-200 font-medium cursor-pointer"
              >
                削除
              </button>
            </div>
          )}
        </div>

        {/* 解決案表示セクション */}
        {(user?.user_type === 'contributor' || (user?.user_type === 'proposer' && userProposal)) && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            {/* ヘッダー：解決案件数とトグルスイッチ */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[1.125rem] font-semibold text-gray-900">
                解決案 ({proposals.length}件)
              </h2>
              
              {/* closed／completed のときトグル（提案者は評価完了かつ分析ありのときのみ） */}
              {(challenge?.status === 'closed' || challenge?.status === 'completed') &&
                ((user?.user_type === 'proposer' && analysis && myInsight && challenge?.has_completed_all_evaluations) ||
                  user?.user_type === 'contributor') && (
                <AnalysisToggleSwitch
                  showAnalysis={showAnalysis}
                  onToggle={setShowAnalysis}
                  isLoading={analysisLoading}
                />
              )}
            </div>
            
            {proposals.length === 0 ? (
              <p className="text-gray-600 text-center py-8">
                まだ解決案が投稿されていません。
              </p>
            ) : user?.user_type === 'proposer' && !userProposal && challenge?.current_phase !== 'proposal' ? (
              // 提案者が未提案で提案期間が過ぎた場合は何も表示しない
              <div className="text-center py-8">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 max-w-md mx-auto">
                  <p className="text-yellow-800 font-medium mb-2">
                    ⚠️ 提案期間が終了しました
                  </p>
                  <p className="text-yellow-700 text-sm">
                    解決案を提案しなかったため、この課題の編集期間・評価期間には参加できません。
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* 提案者向け：自分の提案の分析ビュー */}
                {user?.user_type === 'proposer' && (challenge?.status === 'closed' || challenge?.status === 'completed') && challenge?.has_completed_all_evaluations && analysis && myInsight ? (
                    <>
                    {/* 分析結果または解決案の表示 */}
                    {showAnalysis ? (
                      <ProposerAnalysisSummary
                        analysis={analysis}
                        myInsight={myInsight}
                        myProposalId={userProposal?.id || 0}
                        proposals={proposals}
                        clusteringData={clusteringData}
                        isLoading={analysisLoading}
                      />
                    ) : (
                      <>
                        {/* 自分の解決案（最上位） */}
                        {(() => {
                          // proposalsから自分の提案を取得（proposer_nameが正しく設定されている）
                          const myProposal = proposals.find(p => p.id === userProposal?.id);
                          
                          return myProposal && (
                            <div className="border-2 border-blue-600 rounded-lg p-1">
                              <div className="bg-blue-50 rounded-lg p-4 mb-2">
                                <h3 className="text-sm font-medium text-blue-900 mb-1">あなたの解決案</h3>
                              </div>
                              <ProposalCard
                                proposal={myProposal}
                                showActions={false}
                                showStatus={false}
                                showComments={true}
                                readOnlyComments={true}
                                showChallengeInfo={false}
                                showUserAttributes={true}
                              />
                            </div>
                          );
                        })()}
                        
                        {/* 他の解決案（最新順） */}
                        {(() => {
                          const otherProposals = proposals.filter(p => p.proposer_name !== user?.username)
                            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
                          
                          return otherProposals.length > 0 ? (
                            <>
                              <div className="bg-gray-50 rounded-lg p-4 mb-2 mt-4">
                                <h3 className="text-sm font-medium text-gray-700 mb-1">他の解決案 ({otherProposals.length}件)</h3>
                              </div>
                              {otherProposals.map((proposal) => (
                                <ProposalCard
                                  key={proposal.id}
                                  proposal={proposal}
                                  showActions={false}
                                  showStatus={false}
                                  showComments={true}
                                  readOnlyComments={true}
                                  showChallengeInfo={false}
                                  showUserAttributes={true}
                                />
                              ))}
                            </>
                          ) : null;
                        })()}
                      </>
                    )}
                  </>
                ) : user?.user_type === 'proposer' ? (
                  (() => {
                    // 自分の解決案と他の解決案を分離
                    // proposer_nameフィールドで判定
                    const myProposal = proposals.find((p) =>
                      userProposal ? p.id === userProposal.id : p.proposer_name === user?.username
                    );
                    const otherProposals = proposals.filter(p => p.proposer_name !== user?.username)
                      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
                    const proposerClosedWithoutEval = user?.user_type === 'proposer' && (challenge?.status === 'closed' || challenge?.status === 'completed') && userProposal && !challenge?.has_completed_all_evaluations;
                    
                    return (
                      <>
                        {/* 評価未完了のときの案内 */}
                        {proposerClosedWithoutEval && (
                          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                            <p className="text-amber-800 font-medium">
                              評価が完了していないため、分析結果を閲覧できません。
                            </p>
                          </div>
                        )}
                        {/* 自分の解決案（最上位） */}
                        {myProposal && (
                          <div className="border-2 border-blue-600 rounded-lg p-1">
                            <div className="bg-blue-50 rounded-lg p-4 mb-2">
                              <h3 className="text-sm font-medium text-blue-900 mb-1">あなたの解決案</h3>
                            </div>
                            <ProposalCard
                              key={myProposal.id}
                              proposal={myProposal}
                              showActions={challenge?.status !== 'closed' && challenge?.status !== 'completed'}
                              showStatus={false}
                              showComments={true}
                              readOnlyComments={challenge?.status === 'closed' || challenge?.status === 'completed'}
                              showChallengeInfo={false}
                              showUserAttributes={challenge?.status === 'closed' || challenge?.status === 'completed'}
                              currentPhase={challenge?.current_phase}
                              onComments={(proposal) => {
                                // 提案リスト内の該当提案の未読コメント数を更新
                                if (proposals) {
                                  const updatedProposals = proposals.map(p => 
                                    p.id === proposal.id ? { ...p, unread_comment_count: 0 } : p
                                  );
                                  setProposals(updatedProposals);
                                }
                              }}
                            />
                          </div>
                        )}
                        
                        {/* 他の解決案（最新順） */}
                        {otherProposals.length > 0 && (
                          <>
                            {myProposal && (
                              <div className="bg-gray-50 rounded-lg p-4 mb-2">
                                <h3 className="text-sm font-medium text-gray-700 mb-1">他の解決案 ({otherProposals.length}件)</h3>
                              </div>
                            )}
                            {otherProposals.map((proposal) => (
                              <ProposalCard
                                key={proposal.id}
                                proposal={proposal}
                                showActions={challenge?.status !== 'closed' && challenge?.status !== 'completed'}
                                showStatus={false}
                                showComments={true}
                                readOnlyComments={challenge?.status === 'closed' || challenge?.status === 'completed'}
                                showChallengeInfo={false}
                                showUserAttributes={challenge?.status === 'closed' || challenge?.status === 'completed'}
                                currentPhase={challenge?.current_phase}
                                onComments={(proposal) => {
                                  // 提案リスト内の該当提案の未読コメント数を更新
                                  if (proposals) {
                                    const updatedProposals = proposals.map(p => 
                                      p.id === proposal.id ? { ...p, unread_comment_count: 0 } : p
                                    );
                                    setProposals(updatedProposals);
                                  }
                                }}
                              />
                            ))}
                          </>
                        )}
                      </>
                    );
                  })()
                ) : (
                  // 投稿者：closed／completed でも一覧・分析を表示
                  challenge?.status === 'closed' || challenge?.status === 'completed' ? (
                    <>
                      {adoptionFinalized && (
                        <div className="mb-4 p-4 bg-amber-50 border border-amber-400 rounded-lg">
                          <p className="text-amber-900 font-medium text-center">
                            採用を確定済みです。採用内容の変更はできません。
                          </p>
                        </div>
                      )}
                      {/* 分析結果または解決案一覧の表示 */}
                      {showAnalysis ? (
                        <ChallengeAnalysisSummary
                          analysis={analysis}
                          proposals={proposals}
                          challengeId={challenge.id}
                          isLoading={analysisLoading}
                          onClusteringDataLoaded={(data) => setClusteringData(data)}
                          onAdoptChange={handleAdoptToggle}
                          sharedAdoptionList={adoptionList}
                          sharedSetAdoptionList={setAdoptionList}
                          sharedMemos={adoptionListMemos}
                          sharedSetMemos={setAdoptionListMemos}
                          onOpenAddToAdoptionListModal={(id) => {
                            setAddToAdoptionListModalId(id);
                          }}
                          onConfirmAdoptionFromList={openAdoptionFinalizeConfirm}
                          confirmingAdoption={confirmingAdoption}
                          adoptionFinalized={adoptionFinalized}
                        />
                      ) : (
                        (() => {
                          // 採用された解決案を先頭に並べ、その他は作成日降順
                          const sorted = [...proposals].sort((a, b) => {
                            if (a.is_adopted && !b.is_adopted) return -1;
                            if (!a.is_adopted && b.is_adopted) return 1;
                            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
                          });
                          const totalPages = Math.max(1, Math.ceil(sorted.length / SOLUTION_LIST_PAGE_SIZE));
                          const currentPage = Math.min(solutionListPage, totalPages);
                          const paginatedProposals = sorted.slice(
                            (currentPage - 1) * SOLUTION_LIST_PAGE_SIZE,
                            currentPage * SOLUTION_LIST_PAGE_SIZE
                          );
                          return (
                            <div className="space-y-4">
                              {canManageAdoptionList ? (
                                <p className="text-sm text-gray-600 mb-2">
                                  「採用リスト」に解決案を追加し、必要に応じて「メモ」で備忘を記録したうえで、「採用を確定する」から採用を確定できます。確定前に確認画面が開きます。
                                </p>
                              ) : adoptionFinalized ? (
                                <p className="text-sm text-gray-600 mb-2">
                                  採用は確定済みです（採用マークは閲覧のみ）。
                                </p>
                              ) : null}
                              {paginatedProposals.map((proposal) => {
                                const inList = adoptionList.has(proposal.id);
                                const memoText = adoptionListMemos[String(proposal.id)] ?? '';
                                if (!canManageAdoptionList) {
                                  return (
                                    <ProposalCard
                                      key={proposal.id}
                                      proposal={proposal}
                                      showActions={false}
                                      showStatus={false}
                                      showComments={true}
                                      readOnlyComments={true}
                                      showChallengeInfo={false}
                                      showUserAttributes={true}
                                    />
                                  );
                                }
                                return (
                                  <div key={proposal.id} className="flex gap-3 items-start">
                                    <div className="flex flex-col gap-1.5 flex-shrink-0 pt-2 ml-2 w-[6rem]">
                                      <button
                                        type="button"
                                        onClick={() =>
                                          inList
                                            ? setAdoptionList((prev) => {
                                                const n = new Set(prev);
                                                n.delete(proposal.id);
                                                return n;
                                              })
                                            : (() => {
                                                setAddToAdoptionListModalId(proposal.id);
                                              })()
                                        }
                                        className={`cursor-pointer px-3 py-1.5 rounded-lg text-sm font-medium w-full text-center ${inList ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' : 'bg-green-600 text-white hover:bg-green-700'}`}
                                      >
                                        {inList ? '外す' : '採用リスト'}
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => {
                                          setMemoEditModalProposalId(proposal.id);
                                          setMemoEditModalInput(adoptionListMemos[String(proposal.id)] ?? '');
                                        }}
                                        className={`cursor-pointer px-3 py-1.5 rounded-lg text-sm font-medium w-full text-center border ${memoText ? 'bg-emerald-50 border-emerald-300 text-emerald-800' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
                                      >
                                        メモ{memoText ? ' ✓' : ''}
                                      </button>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <ProposalCard
                                        proposal={proposal}
                                        showActions={false}
                                        showStatus={false}
                                        showComments={true}
                                        readOnlyComments={true}
                                        showChallengeInfo={false}
                                        showUserAttributes={true}
                                      />
                                    </div>
                                  </div>
                                );
                              })}
                              {/* ページネーション */}
                              {totalPages > 1 && (
                                <div className="flex items-center justify-center gap-2 pt-4 border-t border-gray-200 mt-4">
                                  <button
                                    type="button"
                                    onClick={() => setSolutionListPage(p => Math.max(1, p - 1))}
                                    disabled={currentPage <= 1}
                                    className="cursor-pointer px-3 py-1.5 rounded border border-gray-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                                  >
                                    前へ
                                  </button>
                                  <span className="text-sm text-gray-600">
                                    {currentPage} / {totalPages} ページ
                                    <span className="ml-2 text-gray-500">
                                      （全{sorted.length}件、1ページ{SOLUTION_LIST_PAGE_SIZE}件）
                                    </span>
                                  </span>
                                  <button
                                    type="button"
                                    onClick={() => setSolutionListPage(p => Math.min(totalPages, p + 1))}
                                    disabled={currentPage >= totalPages}
                                    className="cursor-pointer px-3 py-1.5 rounded border border-gray-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                                  >
                                    次へ
                                  </button>
                                </div>
                              )}
                            </div>
                          );
                        })()
                      )}
                      {/* 採用リスト（採用確定前のみ・トグルに依存せず最下部に1つ） */}
                      {canManageAdoptionList && adoptionList.size > 0 && (
                        <div className="mt-6 p-5 bg-amber-50/80 border border-amber-200 rounded-xl shadow-sm">
                          <h3 className="text-base font-semibold text-amber-900 mb-4">🛒 採用リスト（{adoptionList.size}件）</h3>
                          <ul className="space-y-4 mb-5">
                            {[...adoptionList].map((pid) => {
                              const p = proposals.find(pr => pr.id === pid);
                              const memo = adoptionListMemos[String(pid)] ?? '';
                              return p ? (
                                <li key={pid} className="flex items-stretch gap-3 rounded-lg border border-amber-200 bg-white p-3 shadow-sm">
                                  {/* 結論・メモを縦に並べたブロック（結論=ピンク、メモ=灰） */}
                                  <div className="flex-1 min-w-0 flex flex-col gap-3">
                                    <div className="rounded-lg p-3 bg-pink-50 border border-pink-200">
                                      <p className="text-xs font-medium text-pink-800 mb-1">【結論】</p>
                                      <p className="text-sm text-gray-800 leading-relaxed">{(p.conclusion || `提案#${pid}`).slice(0, 200)}{(p.conclusion?.length ?? 0) > 200 ? '…' : ''}</p>
                                    </div>
                                    <div className="rounded-lg p-3 bg-gray-100 border border-gray-200 ml-3 sm:ml-4">
                                      <p className="text-xs font-medium text-gray-700 mb-1">メモ：</p>
                                      <p className="text-sm text-gray-700">{memo.trim() ? `${memo.slice(0, 120)}${memo.length > 120 ? '…' : ''}` : '—'}</p>
                                    </div>
                                  </div>
                                  {/* 削除ボタンは横に独立 */}
                                  <div className="flex items-center flex-shrink-0">
                                    <button type="button" onClick={() => setAdoptionList(prev => { const n = new Set(prev); n.delete(pid); return n; })} className="cursor-pointer text-red-600 hover:text-red-800 hover:bg-red-50 text-sm font-medium px-4 py-2 rounded border border-red-200 transition-colors">
                                      削除
                                    </button>
                                  </div>
                                </li>
                              ) : null;
                            })}
                          </ul>
                          <div className="flex justify-end pt-1">
                            <button
                              type="button"
                              disabled={confirmingAdoption}
                              onClick={openAdoptionFinalizeConfirm}
                              className="cursor-pointer px-5 py-2.5 rounded-lg text-sm font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
                            >
                              {confirmingAdoption ? '確定中…' : '採用を確定する'}
                            </button>
                          </div>
                        </div>
                      )}
                      {adoptionFinalizeModalOpen && (
                        <div
                          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4"
                          onClick={() => !confirmingAdoption && setAdoptionFinalizeModalOpen(false)}
                        >
                          <div
                            className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full border border-amber-200"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">採用を確定しますか？</h3>
                            <div className="mb-4 space-y-3 text-sm text-gray-700">
                              <p className="p-3 rounded-md bg-amber-50 border border-amber-300 text-amber-900">
                                確定後は採用の取り消し・やり直しはできません。
                              </p>
                              <p>
                                採用リストの <span className="font-semibold">{adoptionList.size} 件</span>
                                を採用として記録し、課題の状態を「完了」とします。
                              </p>
                            </div>
                            <div className="flex gap-2 justify-end flex-wrap">
                              <button
                                type="button"
                                disabled={confirmingAdoption}
                                onClick={() => void executeFinalizeAdoption()}
                                className="cursor-pointer px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg disabled:opacity-50"
                              >
                                {confirmingAdoption ? '確定中…' : '内容を確認したうえで確定する'}
                              </button>
                              <button
                                type="button"
                                disabled={confirmingAdoption}
                                onClick={() => setAdoptionFinalizeModalOpen(false)}
                                className="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50"
                              >
                                キャンセル
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                      {/* 採用リストに追加モーダル（分析・一覧のどちらから開いた場合も表示） */}
                      {addToAdoptionListModalId != null && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4" onClick={() => { setAddToAdoptionListModalId(null); }}>
                          <div className="bg-white rounded-lg shadow-xl p-7 max-w-md w-full mx-4 border border-gray-200" onClick={(e) => e.stopPropagation()}>
                            <h3 className="text-lg font-semibold text-gray-900 mb-6">採用リストに追加</h3>
                            <div className="flex gap-3 justify-end">
                              <button type="button" onClick={confirmAddToAdoptionList} className="cursor-pointer min-w-[7rem] px-5 py-3 text-base font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg">追加</button>
                              <button type="button" onClick={() => { setAddToAdoptionListModalId(null); }} className="cursor-pointer min-w-[7rem] px-5 py-3 text-base font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg">キャンセル</button>
                            </div>
                          </div>
                        </div>
                      )}
                      {memoEditModalProposalId != null && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4" onClick={() => { setMemoEditModalProposalId(null); setMemoEditModalInput(''); }}>
                          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4 border border-gray-200" onClick={(e) => e.stopPropagation()}>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">メモ</h3>
                            <p className="text-sm text-gray-600 mb-3">
                              採用判断のときの備忘録として入力できます。一覧の「メモ ✓」で後から確認できます。
                            </p>
                            <textarea
                              value={memoEditModalInput}
                              onChange={(e) => setMemoEditModalInput(e.target.value)}
                              className="w-full text-sm border border-gray-300 rounded-lg p-3 min-h-[100px] mb-4 focus:outline-none focus:ring-2 focus:ring-green-500/40"
                              placeholder=""
                              autoFocus
                            />
                            <div className="flex gap-2 justify-end">
                              <button
                                type="button"
                                className="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
                                onClick={() => {
                                  setMemoEditModalProposalId(null);
                                  setMemoEditModalInput('');
                                }}
                              >
                                キャンセル
                              </button>
                              <button type="button" onClick={saveMemoFromModal} className="cursor-pointer px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg">
                                保存
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    // 進行中の課題の場合は通常の解決案一覧表示
                    proposals.map((proposal) => (
                      <ProposalCard
                        key={proposal.id}
                        proposal={proposal}
                        showActions={true}
                        showStatus={false}
                        showComments={true}
                        showChallengeInfo={false}
                        currentPhase={challenge?.current_phase}
                        onComments={(proposal) => {
                          // 提案リスト内の該当提案の未読コメント数を更新
                          if (proposals) {
                            const updatedProposals = proposals.map(p => 
                              p.id === proposal.id ? { ...p, unread_comment_count: 0 } : p
                            );
                            setProposals(updatedProposals);
                          }
                        }}
                      />
                    ))
                  )
                )}
              </div>
            )}

            {challenge?.status === 'completed' && proposals.some((p) => p.is_adopted) && (
              <div className="mt-8 rounded-xl border-2 border-emerald-300 bg-emerald-50/60 p-5 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">採用された解決案</h3>
                <p className="text-sm text-gray-600 mb-4">
                  この課題で採用確定された解決案です。
                </p>
                <div className="space-y-4">
                  {[...proposals]
                    .filter((p) => p.is_adopted)
                    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                    .map((proposal) => (
                      <ProposalCard
                        key={`adopted-${proposal.id}`}
                        proposal={proposal}
                        showActions={false}
                        showStatus={false}
                        showComments={true}
                        readOnlyComments={true}
                        showChallengeInfo={false}
                        showUserAttributes={true}
                      />
                    ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 提案者の未投稿時の案内 */}
        {user?.user_type === 'proposer' && !userProposal && (
          <div className={`border rounded-lg p-4 mb-6 ${
            challenge.current_phase === 'proposal'
              ? 'bg-blue-50 border-blue-200'
              : 'bg-red-50 border-red-300'
          }`}>
            {challenge.current_phase === 'proposal' ? (
              <>
                <p className="text-blue-800 mb-3 text-center">
                  解決案を提案すると、他の提案者の解決案を閲覧できるようになります。
                </p>
                <div className="flex justify-center">
                  <Link
                    href={`/challenges/${challenge.id}/propose`}
                    className="bg-blue-600 text-white px-12 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
                  >
                    解決案を提案
                  </Link>
                </div>
              </>
            ) : (
              <p className="text-red-700 font-medium text-center">
                {challenge.current_phase === 'edit' && '⛔ 編集期間中は新規提案できません。'}
                {challenge.current_phase === 'evaluation' && '⛔ 評価期間中は新規提案できません。'}
                {(challenge.current_phase === 'closed' || challenge.status === 'completed') &&
                  '⛔ この課題の期間が満了しているため、解決案を提案できません。'}
              </p>
            )}
          </div>
        )}

        </div>
      </div>
    </div>
  );
};

export default ChallengeDetailPage;
