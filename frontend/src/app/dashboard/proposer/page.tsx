/**
 * 提案者用ダッシュボードページ
 * 提案者が提案活動の状況を確認できる画面
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import type { ProposalListItem } from '../../../types/proposal';
import type { ChallengeListItem } from '../../../types/challenge';
import { getProposals } from '../../../lib/proposalAPI';
import { getChallenges } from '../../../lib/challengeAPI';
import { useAuth } from '../../../contexts/AuthContext';
import ProposalCard from '../../../components/proposals/ProposalCard';
import ChallengeCard from '../../../components/challenges/ChallengeCard';

const ProposerDashboard: React.FC = () => {
  const { user, token, isAuthenticated } = useAuth();
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);
  const [challenges, setChallenges] = useState<ChallengeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasNewChallenges, setHasNewChallenges] = useState<boolean>(false);

  // ダッシュボードデータの取得
  const fetchDashboardData = async () => {
    console.log('fetchDashboardData called');
    console.log('isAuthenticated:', isAuthenticated);
    console.log('user:', user);
    console.log('token:', token);
    
    // 認証されていない場合はAPI呼び出しを避ける
    if (!isAuthenticated || !user) {
      console.log('Not authenticated, skipping API calls');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // 提案データの取得
      const proposalsResponse = await getProposals();
      console.log('Proposals response:', proposalsResponse);
      const proposalsData = proposalsResponse.results || proposalsResponse || [];
      setProposals(proposalsData);
      
      // 課題データの取得（提案者の場合、選出された課題のみ）
      console.log('Fetching challenges for proposer...');
      console.log('User:', user);
      console.log('Is authenticated:', isAuthenticated);
      console.log('Token:', token);
      const challengesResponse = await getChallenges();
      const challengesData = Array.isArray(challengesResponse) ? challengesResponse : (challengesResponse.results || []);
      
      // 選出された課題（期限切れ以外）に対して提案していない課題があるかチェック
      const hasUnproposedChallenges = challengesData.some(challenge => {
        // 期限切れ課題は除外
        if (challenge.status === 'closed') {
          return false;
        }
        // この課題に対する提案があるかチェック（challengeとchallenge_idの両方をチェック）
        const hasProposal = proposalsData.some(proposal => 
          proposal.challenge === challenge.id || proposal.challenge_id === challenge.id
        );
        return !hasProposal;
      });
      setHasNewChallenges(hasUnproposedChallenges);
      
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
  };

  useEffect(() => {
    if (isAuthenticated && user) {
      fetchDashboardData();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  // 統計情報の計算（安全な処理）
  const totalProposals = proposals?.length || 0;
  const adoptedProposals = proposals?.filter(p => p.is_adopted).length || 0;
  const totalEvaluations = proposals?.reduce((sum, p) => sum + (p.evaluation_count || 0), 0) || 0;
  const averageEvaluation = totalProposals > 0 ? Math.round((totalEvaluations / totalProposals) * 10) / 10 : 0;

  // 課題詳細表示処理
  const handleChallengeView = (challenge: ChallengeListItem) => {
    window.location.href = `/challenges/${challenge.id}`;
  };

  // 最近の提案（提案者自身の提案、最新5件）
  const recentProposals = proposals?.slice(0, 5) || [];
  
  // 未読コメント数の合計
  const totalUnreadComments = proposals?.reduce((sum, p) => sum + (p.unread_comment_count || 0), 0) || 0;
  
  // コメント表示時のコールバック
  const handleComments = (proposal: any) => {
    // 提案リスト内の該当提案の未読コメント数を更新
    if (proposals) {
      const updatedProposals = proposals.map(p => 
        p.id === proposal.id ? { ...p, unread_comment_count: 0 } : p
      );
      setProposals(updatedProposals);
    }
  };
  
  // 評価の多い提案（上位5件）
  const topEvaluatedProposals = proposals
    ?.sort((a, b) => (b.evaluation_count || 0) - (a.evaluation_count || 0))
    .slice(0, 5) || [];

  // 募集中の課題（課題一覧ページの一番上の課題と同じ）
  const openChallenges = React.useMemo(() => {
    if (!challenges || challenges.length === 0) return [];
    
    // 期限切れと募集中を分離
    const expiredChallenges = challenges
      .filter(c => c.status === 'closed')
      .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
    
    const activeChallenges = challenges.filter(c => c.status !== 'closed');
    
    // 提案済みと未提案を分離（募集中は期限が近い順）
    const proposedChallenges = activeChallenges
      .filter(challenge => proposals.some(proposal => proposal.challenge_id === challenge.id))
      .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
    
    const unproposedChallenges = activeChallenges
      .filter(challenge => !proposals.some(proposal => proposal.challenge_id === challenge.id))
      .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
    
    // 優先順位: 未提案 → 提案済み → 期限切れ
    if (unproposedChallenges.length > 0) {
      return [unproposedChallenges[0]];
    } else if (proposedChallenges.length > 0) {
      return [proposedChallenges[0]];
    } else if (expiredChallenges.length > 0) {
      return [expiredChallenges[0]];
    }
    
    return [];
  }, [challenges, proposals]);

  // ローディング表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">ダッシュボード</h1>
            <Link
              href="/challenges"
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200"
            >
              新しい解決案を提案
            </Link>
          </div>
        </div>

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
            <div className="space-y-4">
              {openChallenges.map((challenge) => {
                // この課題に対する提案があるかチェック
                const isProposed = proposals.some(proposal => proposal.challenge_id === challenge.id);
                
                return (
                  <ChallengeCard
                    key={challenge.id}
                    challenge={challenge}
                    showActions={true}
                    userType="proposer"
                    isProposed={isProposed}
                    onView={handleChallengeView}
                  />
                );
              })}
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
                <div className="space-y-4">
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
