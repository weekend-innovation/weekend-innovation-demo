/**
 * 課題詳細ページ
 * 課題の詳細情報を表示
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import type { Challenge } from '../../../types/challenge';
import type { Proposal } from '../../../types/proposal';
import { getChallenge, deleteChallenge } from '../../../lib/challengeAPI';
import { getProposalsByChallenge, getUserProposalForChallenge } from '../../../lib/proposalAPI';
import { useAuth } from '../../../contexts/AuthContext';
import ProposalCard from '../../../components/proposals/ProposalCard';

const ChallengeDetailPage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [userProposal, setUserProposal] = useState<Proposal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const challengeId = params.id as string;

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
        setUserProposal(userProposalData);
        
        // ユーザーが提案済みの場合のみ、他の提案も取得
        if (userProposalData) {
          const proposalsData = await getProposalsByChallenge(parseInt(challengeId));
          setProposals(proposalsData.results);
        }
      }
      
      // 投稿者の場合は全ての解決案を取得
      if (user?.user_type === 'contributor' && isAuthenticated) {
        const proposalsData = await getProposalsByChallenge(parseInt(challengeId));
        setProposals(proposalsData.results);
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
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    });
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
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>投稿者: {challenge.contributor_info?.username || '不明'}</span>
                <span>投稿日: {new Date(challenge.created_at).toLocaleDateString('ja-JP')}</span>
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
                  {formatReward(challenge.reward_amount)}
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
                {formatDeadline(challenge.deadline)}
              </p>
            </div>
          </div>

          {/* 課題内容 */}
          <div className="border-t border-gray-200 pt-4">
            <h2 className="text-[1.3125rem] font-semibold text-gray-900 mb-3">課題内容</h2>
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap pl-4">
                {challenge.description}
              </p>
            </div>
          </div>
        </div>

        {/* 解決案表示セクション */}
        {(user?.user_type === 'contributor' || (user?.user_type === 'proposer' && userProposal)) && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-[1.125rem] font-semibold text-gray-900 mb-4">
              解決案 ({proposals.length}件)
            </h2>
            
            {proposals.length === 0 ? (
              <p className="text-gray-600 text-center py-8">
                まだ解決案が投稿されていません。
              </p>
            ) : (
              <div className="space-y-4">
                {user?.user_type === 'proposer' ? (
                  (() => {
                    // デバッグ: 提案データとユーザー情報を確認
                    console.log('Proposals data:', proposals);
                    console.log('User ID:', user?.id);
                    console.log('First proposal structure:', proposals[0]);
                    console.log('All proposal proposer fields:', proposals.map(p => ({ id: p.id, proposer: p.proposer, proposer_info: p.proposer_info })));
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
                  // 投稿者ユーザーの場合は通常の表示
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
                )}
              </div>
            )}
          </div>
        )}

        {/* 提案者の未投稿時の案内 */}
        {user?.user_type === 'proposer' && !userProposal && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
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
          </div>
        )}

      </div>
    </div>
  );
};

export default ChallengeDetailPage;
