/**
 * アプリケーションレイアウトコンポーネント
 * クライアントサイドでHeaderとメインコンテンツを提供
 */
'use client';

import React from 'react';
import { Header } from './Header';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <>
      <Header />
      <main>
        {children}
      </main>
    </>
  );
};
