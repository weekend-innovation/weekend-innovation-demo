'use client';

import React, { useState, useEffect } from 'react';
import { createReport, checkIfReported, REPORT_REASONS, CreateReportData } from '@/lib/moderationAPI';

interface ReportButtonProps {
  contentType: number;
  objectId: number;
  contentTypeName: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const ReportButton: React.FC<ReportButtonProps> = ({
  contentType,
  objectId,
  contentTypeName,
  className = '',
  size = 'sm'
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedReason, setSelectedReason] = useState('');
  const [description, setDescription] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isReported, setIsReported] = useState(false); // 報告済みかどうか

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base'
  };

  // マウント時に報告済みかどうかを確認
  useEffect(() => {
    const checkReportStatus = async () => {
      const reported = await checkIfReported(contentType, objectId);
      setIsReported(reported);
    };
    
    checkReportStatus();
  }, [contentType, objectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedReason) {
      setErrorMessage('通報理由を選択してください。');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const reportData: CreateReportData = {
        content_type: contentType,
        object_id: objectId,
        reason: selectedReason,
        description: description.trim() || undefined,
      };

      await createReport(reportData);
      
      setSuccessMessage(`${contentTypeName}を通報しました。審査を行います。`);
      setIsReported(true); // 報告済みに設定
      setSelectedReason('');
      setDescription('');
      
      // 3秒後にモーダルを閉じる
      setTimeout(() => {
        setIsModalOpen(false);
        setSuccessMessage('');
      }, 3000);
      
    } catch (error) {
      console.error('Report submission error:', error);
      const errorMsg = error instanceof Error ? error.message : '通報の送信に失敗しました。もう一度お試しください。';
      
      // 「既に報告済み」エラーの場合は報告済みに設定
      if (errorMsg.includes('既に報告済み')) {
        setIsReported(true);
      }
      
      setErrorMessage(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedReason('');
    setDescription('');
    setErrorMessage('');
    setSuccessMessage('');
  };

  return (
    <>
      {/* 通報ボタン */}
      <button
        onClick={(e) => {
          if (isReported) {
            e.preventDefault();
            e.stopPropagation();
            return;
          }
          setIsModalOpen(true);
        }}
        disabled={isReported}
        className={
          isReported
            ? className.replace(/bg-red-\d+/, 'bg-white').replace(/hover:bg-red-\d+/, '').replace(/text-white/, 'text-gray-400') + ' !cursor-not-allowed opacity-60 border-2 border-red-600'
            : className
        }
        style={isReported ? { cursor: 'not-allowed' } : undefined}
        title={isReported ? '報告済み' : `${contentTypeName}を通報する`}
      >
        通報
      </button>

      {/* 報告モーダル */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* ヘッダー */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {contentTypeName}を通報
                </h3>
                <button
                  onClick={handleCloseModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* 成功メッセージ */}
              {successMessage && (
                <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                  {successMessage}
                </div>
              )}

              {/* エラーメッセージ */}
              {errorMessage && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                  {errorMessage}
                </div>
              )}

              {/* フォーム */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* 報告理由 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    通報理由 <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedReason}
                    onChange={(e) => setSelectedReason(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    <option value="">通報理由を選択してください</option>
                    {REPORT_REASONS.map((reason) => (
                      <option key={reason.value} value={reason.value}>
                        {reason.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* 詳細説明 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    詳細説明（任意）
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    placeholder="通報の詳細を記入してください..."
                    maxLength={500}
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    {description.length}/500文字
                  </div>
                </div>

                {/* 注意事項 */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                  <p className="text-sm text-yellow-800">
                    <strong>注意:</strong> 虚偽の通報は禁止されています。
                    通報は適切に審査され、必要に応じて対応いたします。
                  </p>
                </div>

                {/* ボタン */}
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors duration-200"
                    disabled={isSubmitting}
                  >
                    キャンセル
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !selectedReason}
                    className="flex-1 px-4 py-2 text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md transition-colors duration-200"
                  >
                    {isSubmitting ? '送信中...' : '通報する'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
