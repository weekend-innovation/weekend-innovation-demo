/**
 * 認証コンテキスト
 * ユーザーの認証状態とプロフィール情報を管理
 */
'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { User, AuthResponse } from '../types/auth';
import { authAPI } from '../lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState(true);

  // 認証状態の確認（stateから取得）

  // 初期化時にユーザー情報を取得
  useEffect(() => {
    const initAuth = async () => {
      try {
        // トークンが存在するかチェック
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
          console.log('認証トークンなし');
          setIsAuthenticated(false);
          return;
        }
        
        const userData = await authAPI.getProfile();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        // トークンが無効な場合は何もしない
        console.log('認証情報なし');
        setIsAuthenticated(false);
        // 無効なトークンを削除
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // ログイン処理
  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const response: AuthResponse = await authAPI.login({ email, password });
      
      // レスポンスからユーザー情報を設定
      setUser(response.user);
      setIsAuthenticated(true);
      localStorage.setItem('user', JSON.stringify(response.user));
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // ログアウト処理
  const logout = async () => {
    try {
      // サーバーにログアウトを通知
      await authAPI.logout();
    } catch (error) {
      // エラーが発生してもローカルのログアウトは実行
      console.warn('Logout API error (ignored):', error);
    }
    
    // ローカルのトークンとユーザー情報をクリア（必ず実行）
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  // ユーザー情報の更新
  const refreshUser = async () => {
    try {
      const userData = await authAPI.getProfile();
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      // エラーの場合はログアウト
      console.warn('Profile refresh failed:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// カスタムフック
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
