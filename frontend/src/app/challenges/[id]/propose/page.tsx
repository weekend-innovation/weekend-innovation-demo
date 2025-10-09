/**
 * 提案投稿ページ
 * 提案者のみアクセス可能
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import ProposalForm from '@/components/proposals/ProposalForm';
import type { CreateProposalRequest } from '@/types/proposal';
import { createProposal, getUserProposalForChallenge } from '@/lib/proposalAPI';
import { getChallenge } from '@/lib/challengeAPI';
import type { Challenge } from '@/types/challenge';
import type { Proposal } from '@/types/proposal';
import { useAuth } from '@/contexts/AuthContext';

const ProposePage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [existingProposal, setExistingProposal] = useState<Proposal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const challengeId = parseInt(params.id as string);

  // 課題情報と既存提案の取得
  const fetchChallengeData = async () => {
    // 認証されていない場合はAPI呼び出しを避ける
    if (!isAuthenticated || !user) {
      console.log('Not authenticated, skipping API calls');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      // 課題詳細の取得
      const challengeData = await getChallenge(challengeId);
      setChallenge(challengeData);
      
      // 既存の提案を確認
      const userProposal = await getUserProposalForChallenge(challengeId);
      setExistingProposal(userProposal);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (challengeId && isAuthenticated && user) {
      fetchChallengeData();
    } else if (!isAuthenticated) {
      setIsLoading(false);
    }
  }, [challengeId, isAuthenticated, user]);

  // 認証チェック
  if (!isAuthenticated || user?.user_type !== 'proposer') {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              アクセス権限がありません
            </h2>
            <p className="text-yellow-700 mb-4">
              提案の投稿は提案者アカウントでのみ可能です。
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

  // 期限切れの場合の表示（status='closed'）
  if (challenge && challenge.status === 'closed') {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-red-900 mb-2">
              この課題は期限切れです
            </h2>
            <p className="text-red-800 mb-4">
              期限が過ぎているため、解決案を提案することはできません。
            </p>
            <div className="flex gap-4">
              <Link
                href={`/challenges/${challengeId}`}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                課題詳細に戻る
              </Link>
              <Link
                href="/challenges"
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors duration-200"
              >
                課題一覧に戻る
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  // 既存提案がある場合の表示
  if (existingProposal) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              既に提案済みです
            </h2>
            <p className="text-yellow-700 mb-4">
              この課題には既に解決案を投稿しています。1つの課題につき1つの提案のみ投稿できます。
            </p>
            <div className="flex gap-4">
              <Link
                href={`/challenges/${challengeId}`}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                課題詳細に戻る
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 提案投稿処理
  const handleSubmit = async (data: CreateProposalRequest) => {
    try {
      setIsSubmitting(true);
      setError(null);

      const newProposal = await createProposal(data);
      
      // 投稿成功時は課題詳細ページに遷移
      router.push(`/challenges/${challengeId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '提案の投稿に失敗しました');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ローディング表示
  if (isLoading) {
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

  // 課題が募集中でない場合
  if (challenge.status !== 'open') {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">
              この課題は募集中ではありません
            </h2>
            <p className="text-yellow-700 mb-4">
              現在、この課題は{challenge.status === 'closed' ? '締切' : '完了'}しています。
            </p>
            <Link
              href="/challenges"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              他の課題を見る
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          {/* パンくずリスト */}
          <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-4">
            <Link href="/dashboard" className="hover:text-gray-700">
              ダッシュボード
            </Link>
            <span>/</span>
            <Link href="/challenges" className="hover:text-gray-700">
              課題一覧
            </Link>
            <span>/</span>
            <Link href={`/challenges/${challengeId}`} className="hover:text-gray-700">
              課題詳細
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium">解決案を提案</span>
          </nav>
          
          <h1 className="text-3xl font-bold text-gray-900">解決案を提案</h1>
          <p className="mt-2 text-gray-600">
            課題「{challenge?.title || 'この課題'}」に対する解決案を提案してください。
          </p>
        </div>

        {/* 課題情報 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">課題内容</h2>
          <div className="prose max-w-none">
            <p className="text-gray-700 whitespace-pre-wrap">
              {challenge?.description || '課題情報を読み込み中...'}
            </p>
          </div>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">{error}</div>
          </div>
        )}

        {/* 提案フォーム */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <ProposalForm
            challengeId={challengeId}
            onSubmit={handleSubmit}
            isLoading={isSubmitting}
            mode="create"
          />
        </div>
      </div>
    </div>
  );
};

export default ProposePage;
