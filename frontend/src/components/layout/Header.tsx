/**
 * ヘッダーコンポーネント
 * Weekend Innovationプロジェクトのナビゲーション
 * 
 * Phase 1実装内容:
 * - ロゴ表示（Weekend Innovation）
 * - 認証状態に応じたナビゲーションメニュー
 * - ユーザータイプ別ダッシュボードリンク
 * - ログイン・新規登録ボタン（未認証時）
 * - ユーザーメニュー・ログアウト機能（認証時）
 * - レスポンシブ対応（モバイルハンバーガーメニュー）
 */

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { authAPI, tokenManager } from '@/lib/api';
import { useAuth } from '../../contexts/AuthContext';

export function Header() {
  const { user, logout } = useAuth();
  // ハンバーガーメニューの開閉状態
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // ユーザーの状態が変更された時にメニューを閉じる
  useEffect(() => {
    setIsMenuOpen(false);
  }, [user]);

  // ログアウト処理
  const handleLogout = async () => {
    try {
      await logout(); // AuthContextのログアウト関数を呼び出し
      router.push('/');
    } catch (error) {
      console.error('Logout failed:', error);
      // エラーが発生してもホームページにリダイレクト
      router.push('/');
    }
  };

  // ロゴクリック処理
  const handleLogoClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (pathname === '/') {
      // トップページの場合は何もしない
      return;
    } else if (user) {
      // ログイン中はユーザータイプに応じてダッシュボードに遷移
      const dashboardPath = user.user_type === 'contributor' 
        ? '/dashboard/contributor' 
        : '/dashboard/proposer';
      router.push(dashboardPath);
    } else {
      // 未ログインの場合はトップページにリダイレクト
      router.push('/');
    }
  };

  return (
    <header className="bg-black border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* ロゴエリア */}
          <div className="flex items-center">
            <button 
              onClick={handleLogoClick}
              className="flex items-center cursor-pointer"
            >
              <div className="text-2xl font-bold text-white">
                Weekend Innovation
              </div>
            </button>
          </div>

          {/* デスクトップメニュー - 削除（ハンバーガーメニューのみ使用） */}

          {/* デスクトップメニュー（未認証時） - 削除 */}

          {/* ハンバーガーメニューボタン（認証時のみ） */}
          {user && (
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 text-gray-300 hover:text-white cursor-pointer"
            >
              <svg
                className="w-8 h-8"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          )}
        </div>

        {/* サイドメニュー（認証時のみ） */}
        {isMenuOpen && user && (
          <>
            {/* メニュー外のクリック領域 */}
            <div 
              className="fixed inset-0 z-40"
              onClick={() => setIsMenuOpen(false)}
            />
            <div className="fixed right-0 top-0 h-full w-64 bg-white shadow-xl z-50">
              <div className="flex flex-col h-full">
                {/* ヘッダー */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900">メニュー</h2>
                  <button
                    onClick={() => setIsMenuOpen(false)}
                    className="p-2 text-gray-400 hover:text-gray-600 cursor-pointer"
                  >
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                {/* メニューアイテム */}
                <div className="flex-1 py-4">
                  <div className="space-y-2">
                    {user.user_type === 'contributor' && (
                      <>
                        <Link
                          href="/dashboard/contributor" 
                          className="block px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          ダッシュボード
                        </Link>
                        <Link
                          href="/challenges" 
                          className="block px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          課題一覧
                        </Link>
                      </>
                    )}
                    {user.user_type === 'proposer' && (
                      <>
                        <Link
                          href="/dashboard/proposer" 
                          className="block px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          ダッシュボード
                        </Link>
                        <Link
                          href="/proposals" 
                          className="block px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          解決案一覧
                        </Link>
                        <Link
                          href="/challenges" 
                          className="block px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          課題一覧
                        </Link>
                      </>
                    )}
                    <Link
                      href="/profile"
                      className="block px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      プロフィール
                    </Link>
                    <Link
                      href="/settings"
                      className="block px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      設定
                    </Link>
                  </div>
                </div>
                
                {/* フッター */}
                <div className="border-t border-gray-200 p-4">
                  <button
                    onClick={handleLogout}
                    className="w-full block px-4 py-3 text-red-600 hover:bg-red-50 transition-colors rounded-lg"
                  >
                    ログアウト
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </header>
  );
}
