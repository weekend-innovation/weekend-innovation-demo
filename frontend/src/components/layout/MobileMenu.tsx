/**
 * モバイルメニューコンポーネント
 * ハンバーガーメニューでナビゲーションを表示
 */
import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '../../contexts/AuthContext';

const MobileMenu: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  // 投稿者用メニュー
  const contributorMenuItems = [
    { href: '/dashboard/contributor', label: 'ホーム', icon: '📊' },
    { href: '/challenges', label: '課題管理', icon: '📝' },
    { href: '/challenges/create', label: '課題投稿', icon: '➕' },
    { href: '/proposals', label: '提案確認', icon: '💡' },
  ];

  // 提案者用メニュー
  const proposerMenuItems = [
    { href: '/dashboard/proposer', label: 'ホーム', icon: '📊' },
    { href: '/challenges', label: '課題一覧', icon: '📝' },
    { href: '/proposals', label: '提案管理', icon: '💡' },
  ];

  // 共通メニュー
  const commonMenuItems = [
    { href: '/profile', label: 'プロフィール', icon: '👤' },
  ];

  const menuItems = isAuthenticated && user?.user_type === 'contributor' 
    ? [...contributorMenuItems, ...commonMenuItems]
    : isAuthenticated && user?.user_type === 'proposer'
    ? [...proposerMenuItems, ...commonMenuItems]
    : [];

  return (
    <div className="md:hidden">
      {/* ハンバーガーボタン */}
      <button
        onClick={toggleMenu}
        className="text-white hover:text-gray-300 focus:outline-none focus:text-gray-300"
        aria-label="メニューを開く"
      >
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d={isOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"}
          />
        </svg>
      </button>

      {/* メニューオーバーレイ */}
      {isOpen && (
        <div className="fixed inset-0 z-50">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={closeMenu} />
          
          {/* メニューパネル */}
          <div className="fixed top-0 right-0 h-full w-80 bg-white shadow-xl">
            <div className="flex flex-col h-full">
              {/* ヘッダー */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">メニュー</h2>
                <button
                  onClick={closeMenu}
                  className="text-gray-500 hover:text-gray-700"
                  aria-label="メニューを閉じる"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* ユーザー情報 */}
              {isAuthenticated && user && (
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                      <span className="text-gray-600 text-sm font-medium">
                        {user.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">{user.username}</p>
                      <p className="text-xs text-gray-500">
                        {user.user_type === 'contributor' ? '投稿者' : '提案者'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* メニューアイテム */}
              <div className="flex-1 overflow-y-auto">
                <nav className="p-4">
                  {isAuthenticated ? (
                    <div className="space-y-2">
                      {menuItems.map((item) => (
                        <Link
                          key={item.href}
                          href={item.href}
                          onClick={closeMenu}
                          className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 transition-colors duration-200"
                        >
                          <span className="mr-3 text-lg">{item.icon}</span>
                          {item.label}
                        </Link>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Link
                        href="/auth/login"
                        onClick={closeMenu}
                        className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 transition-colors duration-200"
                      >
                        <span className="mr-3 text-lg">🔑</span>
                        ログイン
                      </Link>
                      <Link
                        href="/auth/register"
                        onClick={closeMenu}
                        className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 transition-colors duration-200"
                      >
                        <span className="mr-3 text-lg">📝</span>
                        新規登録
                      </Link>
                    </div>
                  )}
                </nav>
              </div>

              {/* フッター */}
              {isAuthenticated && (
                <div className="p-4 border-t border-gray-200">
                  <button
                    onClick={() => {
                      logout();
                      closeMenu();
                    }}
                    className="w-full flex items-center px-3 py-2 text-sm font-medium text-red-700 rounded-lg hover:bg-red-50 transition-colors duration-200"
                  >
                    <span className="mr-3 text-lg">🚪</span>
                    ログアウト
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MobileMenu;
