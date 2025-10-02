/**
 * コメント返信フォームコンポーネント
 * 提案者のみが返信可能
 */
import React, { useState, useEffect } from 'react';
import type { ProposalCommentReplyFormProps } from '../../types/proposal';

const ProposalCommentReplyForm: React.FC<ProposalCommentReplyFormProps> = ({
  commentId,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  // ローカルストレージから保存された内容を読み込み
  const getStoredContent = () => {
    try {
      const stored = localStorage.getItem(`reply_content_${commentId}`);
      return stored || '';
    } catch {
      return '';
    }
  };

  const [content, setContent] = useState(getStoredContent);

  // 内容が変更されたらローカルストレージに保存
  useEffect(() => {
    try {
      localStorage.setItem(`reply_content_${commentId}`, content);
    } catch {
      // ローカルストレージが使用できない場合は無視
    }
  }, [content, commentId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (content.trim()) {
      onSubmit({ content: content.trim() });
      // 送信成功時にローカルストレージをクリア
      try {
        localStorage.removeItem(`reply_content_${commentId}`);
      } catch {
        // ローカルストレージが使用できない場合は無視
      }
    }
  };

  return (
    <div className="border-l-4 border-blue-200 pl-4 mt-3">
      <h6 className="font-medium text-gray-800 mb-2">返信</h6>
      
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="返信内容を入力してください"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            maxLength={500}
            disabled={isLoading}
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            {content.length}/500文字
          </p>
        </div>

        <div className="flex justify-end gap-2">
          <button
            type="submit"
            disabled={isLoading || !content.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium shadow-sm hover:shadow-md cursor-pointer"
          >
            {isLoading ? '返信中...' : '返信'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium cursor-pointer"
          >
            閉じる
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProposalCommentReplyForm;