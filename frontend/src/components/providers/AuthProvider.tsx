/**
 * 認証プロバイダーコンポーネント
 * クライアントサイドでAuthProviderを提供
 */
'use client';

import React from 'react';
import { AuthProvider } from '../../contexts/AuthContext';

interface AuthProviderWrapperProps {
  children: React.ReactNode;
}

export const AuthProviderWrapper: React.FC<AuthProviderWrapperProps> = ({ children }) => {
  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  );
};
