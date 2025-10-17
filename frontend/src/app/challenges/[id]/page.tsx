/**
 * 課題詳細ページ
 * 課題の詳細情報を表示
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import type { Challenge } from '../../../types/challenge';
import type { Proposal, ProposalListItem } from '../../../types/proposal';
import { getChallenge, deleteChallenge } from '../../../lib/challengeAPI';
import { getProposalsByChallenge, getUserProposalForChallenge } from '../../../lib/proposalAPI';
import { getChallengeAnalysis, getAnalysisStatus, triggerAnalysis, getMyProposalInsight, type ChallengeAnalysisData, type ProposalInsight } from '../../../lib/analyticsAPI';
import { useAuth } from '../../../contexts/AuthContext';
import ProposalCard from '../../../components/proposals/ProposalCard';
import ChallengeAnalysisSummary from '../../../components/analytics/ChallengeAnalysisSummary';
import AnalysisToggleSwitch from '../../../components/analytics/AnalysisToggleSwitch';
import ProposerAnalysisSummary from '../../../components/analytics/ProposerAnalysisSummary';

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
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  
  // 提案者向け分析用のstate
  const [myInsight, setMyInsight] = useState<ProposalInsight | null>(null);
  
  // クラスタリングデータ用のstate
  const [clusteringData, setClusteringData] = useState<any>(null);

  const challengeId = params.id as string;

  // 投稿者向け分析データの取得
  const fetchAnalysisData = async () => {
    if (!challenge || challenge.status !== 'closed') return;
    
    try {
      setAnalysisLoading(true);
      setAnalysisError(null);
      
      const analysisData = await getChallengeAnalysis(parseInt(challengeId));
      setAnalysis(analysisData);
    } catch (error) {
      console.error('分析データ取得エラー:', error);
      setAnalysisError('分析データの取得に失敗しました');
    } finally {
      setAnalysisLoading(false);
    }
  };

  // 提案者向け分析データの取得
  const fetchMyInsightData = async () => {
    console.log('fetchMyInsightData開始', {
      challenge: challenge?.id,
      status: challenge?.status,
      userProposal: userProposal?.id
    });
    
    if (!challenge || challenge.status !== 'closed' || !userProposal) {
      console.log('分析データ取得スキップ:', {
        hasChallenge: !!challenge,
        status: challenge?.status,
        hasUserProposal: !!userProposal
      });
      return;
    }
    
    try {
      setAnalysisLoading(true);
      setAnalysisError(null);
      
      console.log('分析データ取得開始:', challengeId);
      const analysisData = await getChallengeAnalysis(parseInt(challengeId));
      console.log('分析データ取得成功:', analysisData);
      setAnalysis(analysisData);
      
      console.log('提案洞察データ取得開始:', userProposal.id);
      const insightData = await getMyProposalInsight(parseInt(challengeId), userProposal.id);
      console.log('提案洞察データ取得成功:', insightData);
      setMyInsight(insightData);
      
      // クラスタリングデータの取得（提案者用）
      console.log('クラスタリングデータ取得開始');
      try {
        const clusteringResponse = await fetch(
          `http://localhost:8000/api/analytics/challenges/${challengeId}/clustering/`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );
        if (clusteringResponse.ok) {
          const clusteringResult = await clusteringResponse.json();
          console.log('クラスタリングデータ取得成功:', clusteringResult);
          setClusteringData(clusteringResult);
        }
      } catch (clusteringError) {
        console.error('クラスタリングデータ取得エラー:', clusteringError);
        // クラスタリングデータの取得失敗は致命的ではないため、エラーを表示しない
      }
    } catch (error) {
      console.error('提案洞察データ取得エラー:', error);
      setAnalysisError('分析データの取得に失敗しました');
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
  }, [challengeId, isAuthenticated, user]);

  // 分析データの取得（課題データ取得後）
  useEffect(() => {
    console.log('分析データ取得useEffect実行', {
      hasChallenge: !!challenge,
      challengeId: challenge?.id,
      status: challenge?.status,
      userType: user?.user_type,
      hasUserProposal: !!userProposal,
      userProposalId: userProposal?.id
    });
    
    if (challenge && challenge.status === 'closed') {
      if (user?.user_type === 'contributor') {
        console.log('投稿者向け分析データ取得開始');
        // 投稿者向け分析
        fetchAnalysisData();
      } else if (user?.user_type === 'proposer' && userProposal) {
        console.log('提案者向け分析データ取得開始');
        // 提案者向け分析
        fetchMyInsightData();
      }
    } else {
      console.log('分析データ取得条件不一致');
    }
  }, [challenge, userProposal]);

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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
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
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}年${month}月${day}日 ${hours}:${minutes}`;
  };

  // 報酬の表示形式
  const formatReward = (amount: number) => {
    // 0の場合は空文字を返す
    if (amount === 0) {
      return '';
    }
    // 1万円未満の場合は円単位で表示
    if (amount < 10000) {
      return `${amount}円`;
    }
    // 1万円以上の場合は万円単位で表示
    const amountInMan = amount / 10000;
    // 整数の場合は小数点を表示しない
    if (amountInMan % 1 === 0) {
      return `${Math.floor(amountInMan)}万円`;
    }
    // 小数点がある場合は1桁まで表示
    return `${amountInMan.toFixed(1)}万円`;
  };

  // ステータスに応じた表示色とラベル
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'open':
        return { label: '募集中', color: 'text-green-600 bg-green-100' };
      case 'closed':
        return { label: '締切', color: 'text-red-600 bg-red-100' };
      case 'completed':
        return { label: '完了', color: 'text-blue-600 bg-blue-100' };
      default:
        return { label: status, color: 'text-gray-600 bg-gray-100' };
    }
  };

  // 課題が期限切れかどうかを判定
  const isExpired = (deadline: string) => {
    return new Date(deadline) < new Date();
  };

  // ローディング表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
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

  const statusDisplay = getStatusDisplay(challenge.status);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ナビゲーション */}
        {/* パンくずリスト */}
        <div className="mb-6">
          <nav className="flex items-center space-x-2 text-sm text-gray-500">
            <Link href="/dashboard" className="hover:text-gray-700">
              ダッシュボード
            </Link>
            <span>/</span>
            <Link href="/challenges" className="hover:text-gray-700">
              課題一覧
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium">課題詳細</span>
          </nav>
        </div>

        {/* 課題概要と内容（コンパクト） */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="mb-4">
            <div className="flex items-start justify-between mb-2">
              <h1 className="text-[1.3125rem] font-bold text-gray-900 flex-1 pr-4">
                {challenge.title}
              </h1>
              <div className="flex flex-col items-end gap-1 text-sm text-gray-600">
                <span>投稿者: {challenge.contributor_info?.username || '不明'}</span>
                <span>投稿日: {new Date(challenge.created_at).toLocaleDateString('ja-JP')}</span>
                {challenge.updated_at && challenge.updated_at !== challenge.created_at && (
                  <span className="text-xs text-gray-500">編集日時: {new Date(challenge.updated_at).toLocaleDateString('ja-JP')} {new Date(challenge.updated_at).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}</span>
                )}
              </div>
            </div>
          </div>

          {/* 報酬と期限（コンパクト） */}
          <div className="space-y-4 mb-4">
            {/* 報酬情報（2列） */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <p className="text-sm text-blue-600 font-medium mb-1">提案報酬</p>
                <p className="text-lg font-bold text-blue-900">
                  {user?.user_type === 'proposer'
                    ? '6,000円'
                    : formatReward(challenge.reward_amount)
                  }
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-3 text-center">
                <p className="text-sm text-green-600 font-medium mb-1">採用報酬</p>
                <p className="text-lg font-bold text-green-900">
                  {formatReward(challenge.adoption_reward)}
                </p>
              </div>
            </div>
            {/* 期限（1列） */}
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <p className="text-sm text-red-600 font-medium mb-1">期限</p>
              <p className="text-lg font-bold text-red-900">
                {isExpired(challenge.deadline) ? '期限切れ' : formatDeadline(challenge.deadline)}
              </p>
            </div>
          </div>

          {/* 課題内容 */}
          <div className="border-t border-gray-200 pt-4">
            <h2 className="text-[1.1875rem] font-semibold text-gray-900 mb-3">課題内容</h2>
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap pl-4">
                {challenge.description}
              </p>
            </div>
          </div>

          {/* 投稿者のみ編集・削除ボタンを表示（期限切れの課題では編集ボタンを非表示） */}
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
              
              {/* 期限切れ課題の場合のみトグルスイッチを表示 */}
              {challenge?.status === 'closed' && ((user?.user_type === 'proposer' && analysis && myInsight) || (user?.user_type === 'contributor' && analysis)) && (
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
            ) : (
              <div className="space-y-4">
                {/* 提案者向け：期限切れ課題で自分の提案分析を表示 */}
                {user?.user_type === 'proposer' && challenge?.status === 'closed' && analysis && myInsight ? (
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
                    // デバッグ: 提案データとユーザー情報を確認
                    console.log('Proposals data:', proposals);
                    console.log('User ID:', user?.id);
                    console.log('First proposal structure:', proposals[0]);
                    console.log('All proposal proposer fields:', proposals.map(p => ({ id: p.id, proposer_name: p.proposer_name })));
                    console.log('Full proposal structure:', JSON.stringify(proposals[0], null, 2));
                    
                    // 自分の解決案と他の解決案を分離
                    // proposer_nameフィールドで判定
                    const myProposal = proposals.find(p => {
                      console.log(`Checking proposal ${p.id}: proposer_name=${p.proposer_name}, user.username=${user?.username}`);
                      return p.proposer_name === user?.username;
                    });
                    const otherProposals = proposals.filter(p => p.proposer_name !== user?.username)
                      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
                    
                    console.log('My proposal:', myProposal);
                    console.log('Other proposals count:', otherProposals.length);
                    
                    return (
                      <>
                        {/* 自分の解決案（最上位） */}
                        {myProposal && (
                          <div className="border-2 border-blue-600 rounded-lg p-1">
                            <div className="bg-blue-50 rounded-lg p-4 mb-2">
                              <h3 className="text-sm font-medium text-blue-900 mb-1">あなたの解決案</h3>
                            </div>
                            <ProposalCard
                              key={myProposal.id}
                              proposal={myProposal}
                              showActions={true}
                              showStatus={false}
                              showComments={true} // 自分の解決案のコメントも表示可能
                              showChallengeInfo={false}
                              showUserAttributes={challenge?.status === 'closed'}
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
                                showActions={true}
                                showStatus={false}
                                showComments={true}
                                showChallengeInfo={false}
                                showUserAttributes={challenge?.status === 'closed'}
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
                  // 投稿者ユーザーの場合：期限切れ課題では分析機能を表示
                  challenge?.status === 'closed' ? (
                    <>
                      {/* 分析結果または解決案一覧の表示 */}
                      {showAnalysis ? (
                        <ChallengeAnalysisSummary
                          analysis={analysis}
                          proposals={proposals}
                          challengeId={challenge.id}
                          isLoading={analysisLoading}
                          onClusteringDataLoaded={(data) => setClusteringData(data)}
                        />
                      ) : (
                        proposals.map((proposal) => (
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
                        ))
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
          </div>
        )}

        {/* 提案者の未投稿時の案内 */}
        {user?.user_type === 'proposer' && !userProposal && (
          <div className={`border rounded-lg p-4 mb-6 ${
            challenge.status === 'closed' 
              ? 'bg-red-50 border-red-300' 
              : 'bg-blue-50 border-blue-200'
          }`}>
            {challenge.status === 'closed' ? (
              <p className="text-red-700 font-medium text-center">
                ⛔ この課題は期限切れのため、解決案を提案できません。
              </p>
            ) : (
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
            )}
          </div>
        )}

      </div>
    </div>
  );
};

export default ChallengeDetailPage;
