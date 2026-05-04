/**
 * 投稿者用ダッシュボードページ
 * 投稿者が課題と提案の状況を確認できる画面
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { ChallengeListItem } from '../../../types/challenge';
import type { ProposalListItem } from '../../../types/proposal';
import { getAllChallenges } from '../../../lib/challengeAPI';
import { getProposals } from '../../../lib/proposalAPI';
import { sortExpiredChallenges, sortActiveContributorChallenges, isContributorExpired } from '../../../lib/challengeSortUtils';
import { useAuth } from '../../../contexts/AuthContext';
import ProposalCard from '../../../components/proposals/ProposalCard';
import ChallengeCard from '../../../components/challenges/ChallengeCard';
import { DemoVersionModal, DashboardDemoVersionTrigger } from '../../../components/common/DemoVersionNotice';

const ContributorDashboard: React.FC = () => {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authInitializing } = useAuth();
  const [challenges, setChallenges] = useState<ChallengeListItem[]>([]);
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
      
      // 課題データの取得（全件取得でページネーションによる欠落を防ぐ）
      const challengesData = await getAllChallenges();
      setChallenges(challengesData);
      
      // 提案データの取得
      const proposalsResponse = await getProposals();
      setProposals(proposalsResponse.results || proposalsResponse || []);
      
    } catch (err) {
      console.error('Dashboard data fetch error:', err);
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
      // エラー時は空配列を設定
      setChallenges([]);
      setProposals([]);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    if (authInitializing) return;

    if (isAuthenticated && user?.user_type === 'contributor') {
      void fetchDashboardData();
      return;
    }

    if (isAuthenticated && user && user.user_type !== 'contributor') {
      router.replace('/dashboard/proposer');
      return;
    }

    router.replace('/auth/login');
  }, [authInitializing, isAuthenticated, user, fetchDashboardData, router]);

  // 統計情報の計算（安全な処理）
  const totalChallenges = challenges?.length || 0;
  const openChallenges = challenges?.filter(c => !isContributorExpired(c)).length || 0;

  // 最近の課題（一覧と同様に deadline と作成日時で並べ替え）
  const recentChallenges = React.useMemo(() => {
    if (!challenges || challenges.length === 0) return [];
    
    const activeChallenges = sortActiveContributorChallenges(challenges.filter(c => !isContributorExpired(c)));
    const expiredChallenges = sortExpiredChallenges(challenges.filter(c => isContributorExpired(c)));
    
    if (activeChallenges.length > 0) return [activeChallenges[0]];
    if (expiredChallenges.length > 0) return [expiredChallenges[0]];
    return [];
  }, [challenges]);
  
  // 最近の提案（投稿者が投稿した課題に対する提案、最新5件）
  const recentProposals = proposals?.slice(0, 5) || [];
  
  const isContributorSession =
    !authInitializing && isAuthenticated && user?.user_type === 'contributor';

  // 認証初期化中・または未ログイン／別ロール（リダイレクト待ち）はデータ取得前のスピナー
  if (authInitializing || !isContributorSession) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 w-full">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-600">読み込み中...</div>
          </div>
        </div>
      </div>
    );
  }

  // ローディング表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 w-full">
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
            href="/challenges/create"
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 shrink-0"
          >
            新しい課題を投稿
          </Link>
        </div>

        <DemoVersionModal
          isOpen={demoVersionOpen}
          onClose={() => setDemoVersionOpen(false)}
          role="contributor"
        />

        {/* 統計カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-medium">📝</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">総課題数</p>
                <p className="text-2xl font-semibold text-gray-900">{totalChallenges}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-sm font-medium">🟢</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">募集中</p>
                <p className="text-2xl font-semibold text-gray-900">{openChallenges}</p>
              </div>
            </div>
          </div>

        </div>

        <div className="mt-8 space-y-8">
          {/* 最近の課題 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">最近の課題</h2>
              <Link
                href="/challenges"
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                すべて見る
              </Link>
            </div>
            {recentChallenges.length === 0 ? (
              <p className="text-gray-500 text-center py-4">まだ課題を投稿していません</p>
            ) : (
              <div className="space-y-4 max-w-4xl mx-auto px-8 sm:px-10">
                {recentChallenges.map((challenge) => (
                  <ChallengeCard
                    key={challenge.id}
                    challenge={challenge}
                    showActions={true}
                    userType="contributor"
                    onView={(challenge) => {
                      window.location.href = `/challenges/${challenge.id}`;
                    }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* 最近の解決案 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">最近の解決案</h2>
              <Link
                href="/proposals"
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                すべて見る
              </Link>
            </div>
            {recentProposals.length === 0 ? (
              <p className="text-gray-500 text-center py-4">あなたの課題に対する解決案はまだありません</p>
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
                    currentPhase={proposal.challenge_current_phase}
                    readOnlyComments={
                      proposal.challenge_status === 'closed' ||
                      proposal.challenge_status === 'completed'
                    }
                    showUserAttributes={
                      proposal.challenge_status === 'closed' ||
                      proposal.challenge_status === 'completed'
                    }
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

export default ContributorDashboard;
