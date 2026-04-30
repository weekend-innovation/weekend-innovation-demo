/**
 * Weekend Innovation ホームページ
 * 課題解決プラットフォームのランディングページ
 * 
 * Phase 1実装内容:
 * - ヘッダーコンポーネント（認証状態表示・ナビゲーション）
 * - ヒーローセクション（メインタイトル・CTAボタン）
 * - サービス特徴セクション（3つの主要機能説明）
 * - CTAセクション（登録促進）
 * - フッター（著作権表示）
 */

'use client';

import Link from 'next/link';
import { useState } from 'react';
import ServiceDescriptionModal from '../components/common/ServiceDescriptionModal';
import { DemoVersionModal } from '../components/common/DemoVersionNotice';

export default function Home() {
  const [isDescriptionOpen, setIsDescriptionOpen] = useState(false);
  const [isDemoVersionOpen, setIsDemoVersionOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white w-full min-w-0 overflow-x-hidden">
      
      <main>
        {/* ヒーローセクション - メインタイトル・新規登録・ログインボタン */}
        <section className="bg-white pt-32 pb-20">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              {/* メインタイトル */}
              <div className="inline-block relative mb-12">
                <h1 className="text-5xl md:text-7xl font-bold text-black">
                  Weekend Innovation
                </h1>
                <a
                  href="https://note.com/k_kohinata/n/n208bfd8d4450"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="absolute -top-1 -right-5 w-4 h-4 border border-gray-400 text-gray-600 rounded-full hover:border-gray-600 hover:text-gray-800 transition-colors duration-200 flex items-center justify-center text-xs font-bold cursor-pointer"
                  title="サービス理念の記事を開く"
                  aria-label="サービス理念の記事を開く"
                >
                  ?
                </a>
              </div>
              {/* CTAボタン群 - 新規登録・ログイン */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  href="/auth/register"
                  className="bg-black text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors shadow-lg hover:shadow-xl"
                >
                  新規登録
                </Link>
                <Link
                  href="/auth/login"
                  className="border border-black text-black px-8 py-3 rounded-lg font-medium hover:bg-black hover:text-white transition-colors"
                >
                  ログイン
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* サービス特徴セクション - 3つの主要機能を説明 */}
        <section className="bg-gray-50 py-20">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* セクションタイトル */}
            <div className="text-center mb-12">
              <div className="inline-block relative">
                <h2 className="text-3xl font-bold text-black">
                  サービスの特徴
                </h2>
                {/* 説明アイコン */}
                <button
                  onClick={() => setIsDescriptionOpen(true)}
                  className="absolute -top-1 -right-5 w-4 h-4 border border-gray-400 text-gray-600 rounded-full hover:border-gray-600 hover:text-gray-800 transition-colors duration-200 flex items-center justify-center text-xs font-bold cursor-pointer"
                  title="サービスの説明を見る"
                >
                  ?
                </button>
              </div>
            </div>

            {/* 特徴カード群 - 3つの主要機能 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* 課題の投稿カード */}
              <div className="bg-white p-8 rounded-lg shadow-sm">
                <div className="w-12 h-12 bg-black rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-black mb-2">課題の投稿</h3>
                <p className="text-gray-600">
                  企業・自治体などが、多様な視点を必要とする課題を投稿します。
                </p>
              </div>

              {/* ランダム選出カード */}
              <div className="bg-white p-8 rounded-lg shadow-sm">
                <div className="w-12 h-12 bg-black rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-black mb-2">ランダム選出</h3>
                <p className="text-gray-600">
                  投稿された課題に対して解決案を提案する者を、登録している提案者の中からランダムに選出することで、構成の偏りを防ぐことができ、多様な視点の確保につながります。
                </p>
              </div>

              {/* 解決案の提案カード */}
              <div className="bg-white p-8 rounded-lg shadow-sm">
                <div className="w-12 h-12 bg-black rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div className="inline-block relative mb-2">
                  <h3 className="text-xl font-semibold text-black">解決案の提案</h3>
                  <button
                    type="button"
                    onClick={() => setIsDemoVersionOpen(true)}
                    className="absolute -top-1 -right-5 w-4 h-4 border border-gray-400 text-gray-600 rounded-full hover:border-gray-600 hover:text-gray-800 transition-colors duration-200 flex items-center justify-center text-xs font-bold cursor-pointer"
                    title="デモ版の報酬説明を見る"
                    aria-label="デモ版の報酬説明を見る"
                  >
                    ?
                  </button>
                </div>
                <p className="text-gray-600">
                  ランダムに選出された提案者が自身の経験や知識に基づいて解決案を提案します。
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTAセクション - 登録促進・行動喚起 */}
        <section className="bg-black py-20">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            {/* CTAタイトル */}
            <h2 className="text-3xl font-bold text-white mb-4">
              今すぐ始めましょう
            </h2>
            {/* CTA説明文 */}
            <p className="text-gray-300 mb-8 max-w-4xl mx-auto">
              あなたの役割を選択して、実際に体験してみてください。
            </p>
            {/* メインCTAボタン */}
            <Link
              href="/auth/register"
              className="bg-white text-black px-8 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              無料で始める
            </Link>
        </div>
        </section>
      </main>

      {/* フッター - 著作権表示 */}
      <footer className="bg-white border-t border-gray-200 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-600">
            <p>&copy; 2025 Weekend Innovation. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* サービス説明モーダル */}
      <ServiceDescriptionModal 
        isOpen={isDescriptionOpen} 
        onClose={() => setIsDescriptionOpen(false)} 
      />
      <DemoVersionModal
        isOpen={isDemoVersionOpen}
        onClose={() => setIsDemoVersionOpen(false)}
      />
    </div>
  );
}
