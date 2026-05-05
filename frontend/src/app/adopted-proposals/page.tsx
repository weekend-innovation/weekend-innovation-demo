'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getAllProposals } from '@/lib/proposalAPI';
import type { ProposalListItem } from '@/types/proposal';
import ProposalCard from '@/components/proposals/ProposalCard';

const AdoptedProposalsPage: React.FC = () => {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [proposals, setProposals] = useState<ProposalListItem[]>([]);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated || !user) {
      router.replace('/auth/login');
      return;
    }
    if (user.user_type !== 'contributor') {
      router.replace('/dashboard/proposer');
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const all = await getAllProposals();
        setProposals(all);
      } catch (e) {
        console.error('採用済み解決案取得エラー:', e);
        setError(e instanceof Error ? e.message : 'データの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };
    void fetchData();
  }, [authLoading, isAuthenticated, user, router]);

  const adoptedProposals = useMemo(
    () => proposals.filter((p) => p.is_adopted),
    [proposals]
  );

  const groupedByChallenge = useMemo(() => {
    const map = new Map<number, { challengeTitle: string; finalizedAt: string | null; items: ProposalListItem[] }>();
    for (const proposal of adoptedProposals) {
      const existing = map.get(proposal.challenge_id);
      if (!existing) {
        map.set(proposal.challenge_id, {
          challengeTitle: proposal.challenge_title,
          finalizedAt: proposal.challenge_updated_at || null,
          items: [proposal],
        });
      } else {
        existing.items.push(proposal);
        if (!existing.finalizedAt && proposal.challenge_updated_at) {
          existing.finalizedAt = proposal.challenge_updated_at;
        }
      }
    }

    return [...map.entries()]
      .map(([challengeId, value]) => ({
        challengeId,
        challengeTitle: value.challengeTitle,
        finalizedAt: value.finalizedAt,
        items: [...value.items].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ),
      }))
      .sort((a, b) => {
        const ta = a.finalizedAt ? new Date(a.finalizedAt).getTime() : 0;
        const tb = b.finalizedAt ? new Date(b.finalizedAt).getTime() : 0;
        return tb - ta;
      });
  }, [adoptedProposals]);

  if (authLoading || loading) {
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

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 w-full">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mb-4">
        <nav className="flex items-center space-x-2 text-sm text-gray-500">
          <Link href="/dashboard/contributor" className="hover:text-gray-700">
            ホーム
          </Link>
          <span>/</span>
          <span className="text-gray-900 font-medium">採用した解決案</span>
        </nav>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">採用した解決案</h1>
          <p className="mt-2 text-gray-600">採用確定日が新しい課題順に、課題ごとにまとめて表示します。</p>
        </div>

        {adoptedProposals.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500">まだ採用確定された解決案はありません。</p>
          </div>
        ) : (
          <div className="space-y-8">
            {groupedByChallenge.map((group) => (
              <section key={group.challengeId} className="bg-white rounded-lg border border-gray-200 p-5">
                <div className="mb-4 pb-3 border-b border-gray-100">
                  <h2 className="text-lg font-semibold text-gray-900">{group.challengeTitle}</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    採用確定日:{' '}
                    {group.finalizedAt
                      ? new Date(group.finalizedAt).toLocaleString('ja-JP')
                      : '不明'}
                  </p>
                </div>
                <div className="space-y-4">
                  {group.items.map((proposal) => (
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
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdoptedProposalsPage;

