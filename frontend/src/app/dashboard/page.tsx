/**
 * メインダッシュボードページ
 * ユーザータイプに応じて適切なダッシュボードにリダイレクト
 */
'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../contexts/AuthContext';

const DashboardPage: React.FC = () => {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        // 未認証の場合はログインページにリダイレクト
        router.push('/auth/login');
      } else if (user) {
        // 認証済みの場合はユーザータイプに応じてダッシュボードにリダイレクト
        const dashboardPath = user.user_type === 'contributor' 
          ? '/dashboard/contributor' 
          : '/dashboard/proposer';
        router.push(dashboardPath);
      }
    }
  }, [user, isAuthenticated, isLoading, router]);

  // ローディング表示
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="text-gray-600 mb-4">読み込み中...</div>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      </div>
    </div>
  );
};

export default DashboardPage;