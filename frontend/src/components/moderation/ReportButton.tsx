'use client';

import React, { useEffect, useState } from 'react';
import {
  checkIfReported,
  createReport,
  CreateReportData,
  getContentType,
  REPORT_REASONS,
} from '@/lib/moderationAPI';

interface ReportButtonProps {
  contentTypeModel: 'proposal' | 'proposalcomment' | 'proposalcommentreply';
  objectId: number;
  contentTypeName: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const ReportButton: React.FC<ReportButtonProps> = ({
  contentTypeModel,
  objectId,
  contentTypeName,
  className = '',
  size = 'sm',
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedReason, setSelectedReason] = useState('');
  const [description, setDescription] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isReported, setIsReported] = useState(false);
  const [contentTypeId, setContentTypeId] = useState<number | null>(null);
  /** ContentType id 取得の成否（未設定のまま disabled にすると「通報済み」に見えるため分離） */
  const [contentTypeReady, setContentTypeReady] = useState(false);
  const [contentTypeError, setContentTypeError] = useState(false);

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  useEffect(() => {
    const initReportStatus = async () => {
      setContentTypeReady(false);
      setContentTypeError(false);
      setContentTypeId(null);
      try {
        const resolvedTypeId = await getContentType(contentTypeModel);
        setContentTypeId(resolvedTypeId);
        const reported = await checkIfReported(resolvedTypeId, objectId);
        setIsReported(reported);
        setContentTypeReady(true);
      } catch (error) {
        console.error('報告初期化エラー:', error);
        setContentTypeError(true);
      }
    };

    initReportStatus();
  }, [contentTypeModel, objectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedReason) {
      setErrorMessage('通報理由を選択してください。');
      return;
    }
    if (!contentTypeId) {
      setErrorMessage('通報対象の識別情報を取得できませんでした。');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const reportData: CreateReportData = {
        content_type: contentTypeId,
        object_id: objectId,
        reason: selectedReason,
        description: description.trim() || undefined,
      };

      await createReport(reportData);

      setSuccessMessage(`${contentTypeName}を通報しました。審査を行います。`);
      setIsReported(true);
      setSelectedReason('');
      setDescription('');

      setTimeout(() => {
        setIsModalOpen(false);
        setSuccessMessage('');
      }, 3000);
    } catch (error) {
      console.error('Report submission error:', error);
      const errorMsg =
        error instanceof Error
          ? error.message
          : '通報の送信に失敗しました。もう一度お試しください。';

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

  /** 通報済み・読み込み中・ContentType 取得失敗時は押下不可 */
  const isDisabled = !contentTypeReady || contentTypeError || isReported;

  const reportedStyle = `${sizeClasses[size]} ${className
    .replace(/bg-red-\d+/, 'bg-white')
    .replace(/hover:bg-red-\d+/, '')
    .replace(/text-white/, 'text-gray-400')} !cursor-not-allowed opacity-60 border-2 border-red-600`;

  const loadingStyle = `${sizeClasses[size]} bg-gray-100 text-gray-500 border border-gray-300 opacity-80 cursor-wait`;

  const errorStyle = `${sizeClasses[size]} bg-amber-50 text-amber-900 border border-amber-300 cursor-not-allowed`;

  return (
    <>
      <button
        onClick={(e) => {
          if (isReported || contentTypeError || !contentTypeReady) {
            e.preventDefault();
            e.stopPropagation();
            return;
          }
          setIsModalOpen(true);
        }}
        disabled={isDisabled}
        className={
          isReported
            ? reportedStyle
            : contentTypeError
              ? errorStyle
              : !contentTypeReady
                ? loadingStyle
                : `${sizeClasses[size]} cursor-pointer ${className}`.trim()
        }
        style={
          isReported || contentTypeError || !contentTypeReady ? { cursor: 'not-allowed' } : undefined
        }
        title={
          isReported
            ? '報告済み'
            : contentTypeError
              ? '通報の準備に失敗しました（再読み込みしてください）'
              : !contentTypeReady
                ? '通報情報を読み込み中です'
                : `${contentTypeName}を通報する`
        }
      >
        {contentTypeError ? '通報（設定エラー）' : !contentTypeReady ? '通報…' : '通報'}
      </button>

      {isModalOpen && (
        <div
          role="presentation"
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 cursor-pointer"
          onClick={handleCloseModal}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="report-modal-title"
            className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto cursor-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 id="report-modal-title" className="text-lg font-semibold text-gray-900">
                  {contentTypeName}を通報
                </h3>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors rounded p-0.5 cursor-pointer"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {successMessage && (
                <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                  {successMessage}
                </div>
              )}

              {errorMessage && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                  {errorMessage}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    通報理由 <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedReason}
                    onChange={(e) => setSelectedReason(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
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
                  <div className="text-xs text-gray-500 mt-1">{description.length}/500文字</div>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                  <p className="text-sm text-yellow-800">
                    <strong>注意:</strong> 虚偽の通報は禁止されています。
                    通報は適切に審査され、必要に応じて対応いたします。
                  </p>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors duration-200 cursor-pointer disabled:cursor-not-allowed"
                    disabled={isSubmitting}
                  >
                    キャンセル
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !selectedReason}
                    className="flex-1 px-4 py-2 text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md transition-colors duration-200 cursor-pointer"
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
