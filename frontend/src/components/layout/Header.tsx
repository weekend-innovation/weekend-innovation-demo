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

import { useAuth } from '../../contexts/AuthContext';
import ServiceDescriptionModal from '../common/ServiceDescriptionModal';
import { OPEN_SERVICE_DESCRIPTION_EVENT } from '@/lib/openServiceDescription';

export function Header() {
  const { user, logout } = useAuth();
  // ハンバーガーメニューの開閉状態
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  // サービス説明モーダルの開閉状態
  const [isDescriptionOpen, setIsDescriptionOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // ユーザーの状態が変更された時にメニューを閉じる
  useEffect(() => {
    setIsMenuOpen(false);
  }, [user]);

  // デモ版モーダルなどから「サービスの説明」を開く
  useEffect(() => {
    const openServiceDescription = () => setIsDescriptionOpen(true);
    window.addEventListener(OPEN_SERVICE_DESCRIPTION_EVENT, openServiceDescription);
    return () => window.removeEventListener(OPEN_SERVICE_DESCRIPTION_EVENT, openServiceDescription);
  }, []);

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
    <header className="bg-black border-b border-gray-200 w-full">
      <div className="w-full px-4 sm:px-6 lg:px-8">
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
              className="fixed inset-0 z-40 bg-black/35 backdrop-blur-[2px] transition-opacity duration-200"
              onClick={() => setIsMenuOpen(false)}
            />
            <div className="fixed right-0 top-0 z-50 h-full w-72 border-l border-gray-200/80 bg-white/95 shadow-2xl backdrop-blur-xl rounded-l-2xl transition-all duration-200">
              <div className="flex h-full flex-col">
                {/* ヘッダー */}
                <div className="flex items-center justify-between border-b border-gray-100 px-5 py-5">
                  <h2 className="text-xl font-bold tracking-tight text-gray-900">メニュー</h2>
                  <button
                    onClick={() => setIsMenuOpen(false)}
                    className="rounded-lg p-2 text-gray-400 transition-colors duration-200 hover:bg-gray-100 hover:text-gray-700 cursor-pointer"
                    aria-label="メニューを閉じる"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* メニューアイテム */}
                <div className="flex-1 py-3">
                  <div className="space-y-1 px-3">
                    {user.user_type === 'contributor' && (
                      <>
                        <Link
                          href="/dashboard/contributor" 
                          className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          ホーム
                        </Link>
                        <Link
                          href="/challenges" 
                          className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          課題一覧
                        </Link>
                        <Link
                          href="/adopted-proposals"
                          className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          採用した解決案
                        </Link>
                        <span
                          className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-400 cursor-not-allowed line-through"
                        >
                          ウォレット
                        </span>
                      </>
                    )}
                    {user.user_type === 'proposer' && (
                      <>
                        <Link
                          href="/dashboard/proposer" 
                          className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          ホーム
                        </Link>
                        <Link
                          href="/proposals" 
                          className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          解決案一覧
                        </Link>
                        <Link
                          href="/challenges" 
                          className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100"
                          onClick={() => setIsMenuOpen(false)}
                        >
                          課題一覧
                        </Link>
                        <span
                          className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-400 cursor-not-allowed line-through"
                        >
                          ウォレット
                        </span>
                      </>
                    )}
                    <Link
                      href="/profile"
                      className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      プロフィール
                    </Link>
                    <Link
                      href="/qa"
                      className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      Q&A
                    </Link>
                    <span
                      className="block rounded-xl px-4 py-3.5 text-[15px] font-medium leading-snug text-gray-400 cursor-not-allowed line-through"
                    >
                      設定
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setIsDescriptionOpen(true);
                        setIsMenuOpen(false);
                      }}
                      className="w-full rounded-xl px-4 py-3.5 text-left text-[15px] font-medium leading-snug text-gray-800 transition-colors duration-200 hover:bg-gray-100 cursor-pointer"
                    >
                      サービスの説明
                    </button>
                  </div>
                </div>
                
                {/* フッター */}
                <div className="border-t border-gray-100 p-4">
                  <button
                    onClick={handleLogout}
                    className="w-full rounded-xl px-4 py-3 text-red-600 transition-all duration-200 hover:bg-red-50 hover:text-red-700 hover:font-semibold cursor-pointer"
                  >
                    ログアウト
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* サービス説明モーダル */}
      <ServiceDescriptionModal 
        isOpen={isDescriptionOpen} 
        onClose={() => setIsDescriptionOpen(false)} 
      />
    </header>
  );
}
