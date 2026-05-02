'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { qaAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type { QaQuestion } from '@/types/qa';

const QaPage = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [questions, setQuestions] = useState<QaQuestion[]>([]);
  const [questionText, setQuestionText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQuestions = async () => {
    try {
      setLoadingQuestions(true);
      setError(null);
      const data = await qaAPI.listQuestions();
      setQuestions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Q&Aの取得に失敗しました。');
    } finally {
      setLoadingQuestions(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated || !user) return;
    void fetchQuestions();
  }, [isAuthenticated, user]);

  const handleSubmitQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = questionText.trim();
    if (text.length < 5) {
      alert('質問は5文字以上で入力してください。');
      return;
    }
    if (text.length > 2000) {
      alert('質問は2000文字以内で入力してください。');
      return;
    }
    try {
      setSubmitting(true);
      await qaAPI.createQuestion({ question_text: text });
      setQuestionText('');
      await fetchQuestions();
      alert('質問を送信しました。回答までしばらくお待ちください。');
    } catch (err) {
      alert(err instanceof Error ? err.message : '質問送信に失敗しました。');
    } finally {
      setSubmitting(false);
    }
  };

  const publicAnswered = useMemo(
    () =>
      questions.filter(
        (q) => q.status === 'answered' && q.is_public && q.answer_text?.trim().length > 0
      ),
    [questions]
  );

  const myPending = useMemo(() => {
    if (!user) return [];
    const myNumericId = Number(user.id);
    if (!Number.isFinite(myNumericId)) return [];
    return questions.filter(
      (q) =>
        q.asked_by === myNumericId &&
        (q.status === 'pending' || !q.answer_text?.trim())
    );
  }, [questions, user]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-yellow-800 mb-2">ログインが必要です</h2>
            <p className="text-yellow-700 mb-4">Q&Aページの利用にはログインが必要です。</p>
            <Link
              href="/auth/login"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              ログイン
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Q&A</h1>
          <p className="mt-2 text-gray-600">
            デモ版についての質問や改善要望を送信できます。回答済みで公開された内容のみ全体表示されます。
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">質問を送信する</h2>
          <form onSubmit={handleSubmitQuestion} className="space-y-3">
            <textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              rows={5}
              maxLength={2000}
              placeholder="確認したいこと・改善してほしいことをご記入ください（5文字～2000文字）"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500">{questionText.length}/2000文字</p>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={submitting}
                className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {submitting ? '送信中...' : '質問を送信'}
              </button>
            </div>
          </form>
        </div>

        {myPending.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-8">
            <h3 className="text-sm font-semibold text-amber-900 mb-2">あなたの回答待ち質問</h3>
            <ul className="space-y-2 text-sm text-amber-900">
              {myPending.map((q) => (
                <li key={q.id}>- {q.question_text}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">公開Q&A</h2>
          {loadingQuestions ? (
            <p className="text-gray-600">読み込み中...</p>
          ) : error ? (
            <p className="text-red-600">{error}</p>
          ) : publicAnswered.length === 0 ? (
            <p className="text-gray-500">公開中のQ&Aはまだありません。</p>
          ) : (
            <div className="space-y-6">
              {publicAnswered.map((q) => (
                <div key={q.id} className="border border-gray-200 rounded-lg p-4">
                  <p className="font-medium text-gray-900 whitespace-pre-wrap">{q.question_text}</p>
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-xs text-gray-600 mb-2">
                      {q.answered_by_username || '管理者'}による回答
                    </p>
                    <p className="text-gray-800 whitespace-pre-wrap">{q.answer_text}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QaPage;

