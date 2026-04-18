/**
 * 提案者用ダッシュボードページ
 * 提案者が提案活動の状況を確認できる画面
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import type { ProposalListItem } from '../../../types/proposal';
import type { ChallengeListItem } from '../../../types/challenge';
import { getProposals } from '../../../lib/proposalAPI';
import { getAllChallenges } from '../../../lib/challengeAPI';
import { sortExpiredChallenges, sortActiveProposerChallenges, isProposerExpiredOrFailed } from '../../../lib/challengeSortUtils';
import { useAuth } from '../../../contexts/AuthContext';
import ProposalCard from '../../../components/proposals/ProposalCard';
import ChallengeCard from '../../../components/challenges/ChallengeCard';
import { DemoVersionModal, DashboardDemoVersionTrigger } from '../../../components/common/DemoVersionNotice';

const ProposerDashboard: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);
  const [challenges, setChallenges] = useState<ChallengeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasNewChallenges, setHasNewChallenges] = useState<boolean>(false);
  const [demoVersionOpen, setDemoVersionOpen] = useState(false);

  // ダッシュボードデータの取得
  const fetchDashboardData = useCallback(async () => {
    // 認証されていない場合はAPI呼び出しを避ける
    if (!isAuthenticated || !user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // 提案データの取得
      const proposalsResponse = await getProposals();
      const proposalsData = proposalsResponse.results || proposalsResponse || [];
      setProposals(proposalsData);
      
      // 課題データの取得（提案者の場合、選出された課題のみ。全件取得でページネーションによる欠落を防ぐ）
      const challengesData = await getAllChallenges();
      
      // 選出された課題のうち、行う作業が残っているものが存在するか
      // ① 未提案（提案期間）② 評価未完了（評価期間）。編集期間の編集は任意のため対象外
      const hasWorkRemaining = challengesData.some(c => {
        if (isProposerExpiredOrFailed(c)) return false;
        if (!c.has_proposed) return true; // 提案が必要
        if (c.current_phase === 'evaluation' && !c.has_completed_all_evaluations) return true; // 評価が必要
        return false;
      });
      setHasNewChallenges(hasWorkRemaining);
      
      setChallenges(challengesData);
      
    } catch (err) {
      console.error('Dashboard data fetch error:', err);
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
      // エラー時は空配列を設定
      setProposals([]);
      setChallenges([]);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    if (isAuthenticated && user) {
      void fetchDashboardData();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated, user, fetchDashboardData]);

  // 統計情報の計算（安全な処理）
  const totalProposals = proposals?.length || 0;
  const adoptedProposals = proposals?.filter(p => p.is_adopted).length || 0;

  // 課題詳細表示処理
  const handleChallengeView = (challenge: ChallengeListItem) => {
    window.location.href = `/challenges/${challenge.id}`;
  };

  // 最近の提案（提案者自身の提案、最新5件）
  const recentProposals = proposals?.slice(0, 5) || [];
  
  // 未読コメント数の合計
  const totalUnreadComments = proposals?.reduce((sum, p) => sum + (p.unread_comment_count || 0), 0) || 0;
  
  // コメント表示時のコールバック
  const handleComments = (proposal: ProposalListItem) => {
    // 提案リスト内の該当提案の未読コメント数を更新
    if (proposals) {
      const updatedProposals = proposals.map(p => 
        p.id === proposal.id ? { ...p, unread_comment_count: 0 } : p
      );
      setProposals(updatedProposals);
    }
  };
  
  // 評価の多い提案（上位5件）

  // 募集中の課題（課題一覧と同じ: 期限切れ扱いでないもの＝次のフェーズまで近い順、期限切れ＝直近終了順）
  const openChallenges = React.useMemo(() => {
    if (!challenges || challenges.length === 0) return [];
    
    const expiredChallenges = sortExpiredChallenges(challenges.filter(c => isProposerExpiredOrFailed(c)));
    const activeChallenges = sortActiveProposerChallenges(challenges.filter(c => !isProposerExpiredOrFailed(c)));
    
    if (activeChallenges.length > 0) return [activeChallenges[0]];
    if (expiredChallenges.length > 0) return [expiredChallenges[0]];
    return [];
  }, [challenges]);

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
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">{error}</div>
            <button
              onClick={fetchDashboardData}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
            >
              再試行
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 w-full">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ページヘッダー */}
        <div className="mb-8 flex flex-wrap justify-between items-start gap-4">
          <DashboardDemoVersionTrigger onOpen={() => setDemoVersionOpen(true)} />
          <Link
            href="/challenges"
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200 shrink-0"
          >
            新しい解決案を提案
          </Link>
        </div>

        <DemoVersionModal
          isOpen={demoVersionOpen}
          onClose={() => setDemoVersionOpen(false)}
          role="proposer"
        />

        {/* 統計カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-medium">💡</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">総提案数</p>
                <p className="text-2xl font-semibold text-gray-900">{totalProposals}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-sm font-medium">✅</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">採用数</p>
                <p className="text-2xl font-semibold text-gray-900">{adoptedProposals}</p>
              </div>
            </div>
          </div>

        </div>


        {/* 募集中の課題 */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">募集中の課題</h2>
            <Link
              href="/challenges"
              className="text-blue-600 hover:text-blue-800 text-sm font-medium relative inline-block"
            >
              すべて見る
              {hasNewChallenges && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              )}
            </Link>
          </div>
          {openChallenges.length === 0 ? (
            <p className="text-gray-500 text-center py-4">現在、募集中の課題はありません</p>
          ) : (
            <div className="space-y-4 max-w-4xl mx-auto px-8 sm:px-10">
              {openChallenges.map((challenge) => (
                <ChallengeCard
                  key={challenge.id}
                  challenge={challenge}
                  showActions={true}
                  userType="proposer"
                  isProposed={!!challenge.has_proposed}
                  onView={handleChallengeView}
                />
              ))}
            </div>
          )}
        </div>

        <div className="mt-8 space-y-8">
            {/* 最近の解決案 */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-900">最近の解決案</h2>
                <Link
                  href="/proposals"
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium relative inline-block"
                >
                  すべて見る
                  {totalUnreadComments > 0 && (
                    <span className="absolute -top-1 -right-3 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {totalUnreadComments}
                    </span>
                  )}
                </Link>
              </div>
              {recentProposals.length === 0 ? (
                <p className="text-gray-500 text-center py-4">まだ解決案を提案していません</p>
              ) : (
                <div className="space-y-4 max-w-4xl mx-auto px-8 sm:px-10">
                  {recentProposals.map((proposal) => (
                    <ProposalCard
                      key={proposal.id}
                      proposal={proposal}
                      showActions={false}
                      showStatus={false}
                      showComments={true}
                      showChallengeInfo={true}
                      onComments={handleComments}
                    />
                  ))}
                </div>
              )}
            </div>

        </div>
      </div>
    </div>
  );
};

export default ProposerDashboard;
