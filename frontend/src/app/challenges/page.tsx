/**
 * 課題一覧ページ
 * ユーザータイプに応じて表示内容を変更
 */
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import ChallengeCard from '../../components/challenges/ChallengeCard';
import type { ChallengeListItem, ChallengeListResponse } from '../../types/challenge';
import { getChallenges, deleteChallenge } from '../../lib/challengeAPI';
import { getUserProposalForChallenge } from '../../lib/proposalAPI';
import { useAuth } from '../../contexts/AuthContext';

const ChallengesPage: React.FC = () => {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [challenges, setChallenges] = useState<ChallengeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userProposals, setUserProposals] = useState<{[key: number]: any}>({});

  // 課題一覧の取得
  const fetchChallenges = async () => {
    // 認証されていない場合はAPI呼び出しを避ける
    if (!isAuthenticated || !user) {
      console.log('Not authenticated, skipping API calls');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response: any = await getChallenges();
      
      // レスポンスが配列の場合とオブジェクトの場合を両方処理
      let challengesData = [];
      if (Array.isArray(response)) {
        challengesData = response;
      } else if (response && response.results) {
        challengesData = response.results;
      }
      
      // 提案者ユーザーの場合、各課題の提案状況をチェック
      if (user.user_type === 'proposer') {
        const proposalStatus: {[key: number]: any} = {};
        for (const challenge of challengesData) {
          try {
            const proposal = await getUserProposalForChallenge(challenge.id);
            if (proposal) {
              proposalStatus[challenge.id] = proposal;
            }
          } catch (err) {
            // 提案がない場合は無視
            console.log(`No proposal found for challenge ${challenge.id}`);
          }
        }
        setUserProposals(proposalStatus);
      }
      
      // 期限順（期限が近いものが上に来る順）でソート
      challengesData.sort((a: ChallengeListItem, b: ChallengeListItem) => {
        const deadlineA = new Date(a.deadline);
        const deadlineB = new Date(b.deadline);
        return deadlineA.getTime() - deadlineB.getTime();
      });
      
      // デバッグ: 報酬データを確認
      console.log('Challenge reward data:', challengesData.map((c: ChallengeListItem) => ({
        id: c.id,
        title: c.title,
        reward_amount: c.reward_amount,
        adoption_reward: c.adoption_reward,
        reward_amount_man: Math.floor(c.reward_amount / 10000),
        adoption_reward_man: Math.floor(c.adoption_reward / 10000)
      })));
      
      setChallenges(challengesData);
    } catch (err) {
      console.error('課題一覧取得エラー:', err);
      setError(err instanceof Error ? err.message : '課題の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 認証されている場合のみ課題一覧を取得
    if (isAuthenticated && user) {
      fetchChallenges();
    } else if (!isAuthenticated) {
      setLoading(false);
      setError('ログインが必要です');
    }
  }, [isAuthenticated, user]);

  // ページフォーカス時に課題一覧を更新
  useEffect(() => {
    const handleFocus = () => {
      if (isAuthenticated && user) {
        fetchChallenges();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [isAuthenticated, user]);

  // 課題カードのクリック処理
  const handleChallengeView = (challenge: ChallengeListItem) => {
    // 課題詳細ページに遷移
    window.location.href = `/challenges/${challenge.id}`;
  };

  // 課題編集処理（投稿者のみ）
  const handleChallengeEdit = (challenge: ChallengeListItem) => {
    if (user?.user_type === 'contributor') {
      window.location.href = `/challenges/${challenge.id}/edit`;
    }
  };

  // 課題削除処理（投稿者のみ）
  const handleChallengeDelete = async (challenge: ChallengeListItem) => {
    if (user?.user_type === 'contributor' && confirm('この課題を削除しますか？')) {
      try {
        await deleteChallenge(challenge.id);
        console.log('課題削除成功:', challenge.id);
        // 削除後に課題一覧を再取得
        fetchChallenges();
      } catch (error) {
        console.error('課題削除エラー:', error);
        alert('課題の削除に失敗しました。');
      }
    }
  };

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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              ログインが必要です
            </h2>
            <p className="text-yellow-700 mb-4">
              課題一覧を表示するにはログインしてください。
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
              onClick={fetchChallenges}
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
          {/* パンくずリスト */}
          <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-4">
            <Link href="/dashboard" className="hover:text-gray-700">
              ダッシュボード
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium">
              {user?.user_type === 'contributor' ? '投稿した課題' : '課題一覧'}
            </span>
          </nav>
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {user?.user_type === 'contributor' ? '投稿した課題' : '課題一覧'}
              </h1>
              <p className="mt-2 text-gray-600">
                {user?.user_type === 'contributor' 
                  ? 'あなたが投稿した課題の一覧です'
                  : '参加可能な課題の一覧です'
                }
              </p>
            </div>
            
            {/* 投稿者のみ課題作成ボタンを表示 */}
            {user?.user_type === 'contributor' && (
              <Link
                href="/challenges/create"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                新しい課題を投稿
              </Link>
            )}
          </div>
        </div>

        {/* 課題一覧 */}
        {!challenges || challenges.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">
              {user?.user_type === 'contributor' 
                ? 'まだ課題を投稿していません'
                : '現在、参加可能な課題はありません'
              }
            </div>
            {user?.user_type === 'contributor' && (
              <Link
                href="/challenges/create"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                最初の課題を投稿
              </Link>
            )}
          </div>
        ) : (
          <div className="max-w-4xl mx-auto px-4">
            <div className="space-y-6">
              {(() => {
                if (user?.user_type === 'proposer') {
                  // 提案者ユーザーの場合、募集中（未提案→提案済み）を期限が近い順、期限切れは後回し
                  const expiredChallenges = challenges
                    .filter(challenge => challenge.status === 'closed')
                    .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
                  
                  const activeChallenges = challenges.filter(challenge => challenge.status !== 'closed');
                  
                  const proposedChallenges = activeChallenges
                    .filter(challenge => userProposals[challenge.id])
                    .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
                  
                  const unproposedChallenges = activeChallenges
                    .filter(challenge => !userProposals[challenge.id])
                    .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
                  
                  return (
                    <>
                      {/* 未提案の課題（募集中） */}
                      {unproposedChallenges.map((challenge) => (
                        <ChallengeCard
                          key={challenge.id}
                          challenge={challenge}
                          showActions={true}
                          userType="proposer"
                          onView={handleChallengeView}
                        />
                      ))}
                      
                      {/* 提案済みの課題 */}
                      {proposedChallenges.map((challenge) => (
                        <ChallengeCard
                          key={challenge.id}
                          challenge={challenge}
                          showActions={true}
                          userType="proposer"
                          isProposed={true}
                          onView={handleChallengeView}
                        />
                      ))}
                      
                      {/* 期限切れの課題 */}
                      {expiredChallenges.map((challenge) => (
                        <ChallengeCard
                          key={challenge.id}
                          challenge={challenge}
                          showActions={true}
                          userType="proposer"
                          onView={handleChallengeView}
                        />
                      ))}
                    </>
                  );
                } else {
                  // 投稿者ユーザーの場合、募集中を期限が近い順、期限切れは後回し
                  const activeChallenges = challenges
                    .filter(challenge => challenge.status !== 'closed')
                    .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
                  
                  const expiredChallenges = challenges
                    .filter(challenge => challenge.status === 'closed')
                    .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
                  
                  const sortedChallenges = [...activeChallenges, ...expiredChallenges];
                  
                  return sortedChallenges.map((challenge) => (
                    <ChallengeCard
                      key={challenge.id}
                      challenge={challenge}
                      showActions={true}
                      userType="contributor"
                      onView={handleChallengeView}
                    />
                  ));
                }
              })()}
            </div>
          </div>
        )}

        {/* ページネーション（TODO: 実装予定） */}
        {challenges && challenges.length > 0 && (
          <div className="mt-8 flex justify-center">
            <div className="text-gray-600 text-sm">
              表示中: {challenges.length}件
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChallengesPage;
