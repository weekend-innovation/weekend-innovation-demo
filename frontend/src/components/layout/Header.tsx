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

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authAPI, tokenManager } from '@/lib/api';
import { User } from '@/types/auth';

interface HeaderProps {
  user?: User | null;
}

export function Header({ user }: HeaderProps) {
  // モバイルメニューの開閉状態
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  // ユーザーメニューの開閉状態
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const router = useRouter();

  // ログアウト処理
  const handleLogout = async () => {
    try {
      await authAPI.logout();
      router.push('/');
      router.refresh();
    } catch (error) {
      console.error('Logout failed:', error);
      // エラーが発生してもローカルのトークンを削除
      tokenManager.clearTokens();
      router.push('/');
      router.refresh();
    }
  };

  return (
    <header className="bg-black border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* ロゴエリア */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <div className="text-2xl font-bold text-white">
                Weekend Innovation
              </div>
            </Link>
          </div>

          {/* デスクトップメニュー */}
          <nav className="hidden md:flex items-center space-x-8">
            {user && (
              <>
                {user.user_type === 'contributor' && (
                  <Link 
                    href="/contributor/dashboard" 
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    ダッシュボード
                  </Link>
                )}
                {user.user_type === 'proposer' && (
                  <Link 
                    href="/proposer/dashboard" 
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    ダッシュボード
                  </Link>
                )}
              </>
            )}
          </nav>

          {/* ユーザーメニュー */}
          <div className="flex items-center space-x-4">
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center text-gray-300 hover:text-white transition-colors"
                >
                  <span className="mr-2">
                    {user.user_type === 'contributor' ? '投稿者' : '提案者'}
                  </span>
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-50">
                    <div className="py-1">
                      <Link
                        href="/profile"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setIsUserMenuOpen(false)}
                      >
                        プロフィール
                      </Link>
                      <Link
                        href="/settings"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setIsUserMenuOpen(false)}
                      >
                        設定
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        ログアウト
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  href="/auth/register"
                  className="bg-white text-black px-4 py-2 rounded hover:bg-gray-100 transition-colors"
                >
                  新規登録
                </Link>
                <Link
                  href="/auth/login"
                  className="border border-white text-white px-4 py-2 rounded hover:bg-white hover:text-black transition-colors"
                >
                  ログイン
                </Link>
              </div>
            )}

            {/* モバイルメニューボタン */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 text-gray-300 hover:text-white"
            >
              <svg
                className="w-6 h-6"
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
          </div>
        </div>

        {/* モバイルメニュー */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-gray-700">
            <div className="py-4 space-y-4">
              {user && (
                <>
                  {user.user_type === 'contributor' && (
                    <Link
                      href="/contributor/dashboard"
                      className="block text-gray-300 hover:text-white transition-colors"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      ダッシュボード
                    </Link>
                  )}
                  {user.user_type === 'proposer' && (
                    <Link
                      href="/proposer/dashboard"
                      className="block text-gray-300 hover:text-white transition-colors"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      ダッシュボード
                    </Link>
                  )}
                  <Link
                    href="/profile"
                    className="block text-gray-300 hover:text-white transition-colors"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    プロフィール
                  </Link>
                  <Link
                    href="/settings"
                    className="block text-gray-300 hover:text-white transition-colors"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    設定
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="block text-gray-300 hover:text-white transition-colors"
                  >
                    ログアウト
                  </button>
                </>
              )}
              
              {!user && (
                <>
                  <Link
                    href="/auth/register"
                    className="block text-gray-300 hover:text-white transition-colors"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    新規登録
                  </Link>
                  <Link
                    href="/auth/login"
                    className="block text-gray-300 hover:text-white transition-colors"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    ログイン
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
