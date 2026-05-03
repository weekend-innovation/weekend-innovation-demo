'use client';

import React from 'react';
import { DEMO_REWARD_PAYMENT_NOTICE } from './DemoVersionNotice';

interface ServiceDescriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ServiceDescriptionModal: React.FC<ServiceDescriptionModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="bg-white rounded max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-gray-300"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="service-description-modal-title"
      >
        <div className="sticky top-0 bg-white border-b border-gray-300 px-6 py-3 flex items-center justify-between">
          <h2 id="service-description-modal-title" className="text-xl font-bold text-gray-900">
            サービスの説明
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl cursor-pointer"
            aria-label="閉じる"
          >
            ✕
          </button>
        </div>

        <div className="px-6 py-6 space-y-5">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">サービス概要</h3>
            <p className="text-gray-700 text-sm leading-relaxed indent-4">
              Weekend Innovationは、企業や自治体などが抱える課題に対して、世界中の多様な提案者から革新的な解決案を募集するプラットフォームです。
            </p>
            <p className="text-gray-700 text-sm leading-relaxed mt-2 indent-4">
              提案者の選出はシステムによるランダム選出で行い、期限後にAIが集まった解決案を整理・分析することで、従来の発想にとらわれない新しい解決策の発見を支援します。
            </p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">サービスの流れ</h3>
            <div className="space-y-3">
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 border-2 border-gray-800 text-gray-800 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    1
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">課題の投稿（投稿者）</h4>
                </div>
                <p className="text-gray-600 text-xs mb-1 indent-4">
                  投稿者（企業や自治体）が、新規事業や新商品・サービスに関する課題を投稿します。
                </p>
                <p className="text-gray-600 text-xs indent-4">
                  その際、投稿者は、他にも提案報酬の総額、採用報酬及び期限を設定します。
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 border-2 border-gray-800 text-gray-800 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    2
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">提案者の選出</h4>
                </div>
                <p className="text-gray-600 text-xs mb-1 indent-4">
                  システムが、登録している提案者の中から、その課題に対する解決案を提出する提案者をランダムに選出します。
                </p>
                <p className="text-gray-600 text-xs indent-4">
                  結果として、属性の偏りが生じにくく、多様な視点を集めやすくなります。
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 border-2 border-gray-800 text-gray-800 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    3
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">提案期間（提案者）</h4>
                </div>
                <p className="text-gray-600 text-xs mb-1 indent-4">
                  選出された提案者が、その課題に対する解決案（結論・理由）を提出します。
                </p>
                <p className="text-gray-600 text-xs indent-4">
                  なお、提案者の属性情報（国籍・性別・年齢）は、課題の募集期限の満了までは公開されず、代わりの名前（Lion、Tigerなど）が割り当てられます。これにより、偏見のない公平な議論と評価を実現します。
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 border-2 border-gray-800 text-gray-800 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    4
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">編集期間（提案者間）</h4>
                </div>
                <p className="text-gray-600 text-xs mb-1 indent-4">
                  解決案を提出した提案者は、提案期間・編集期間の両方で、他の提案者の解決案にコメントを送ることができます。
                </p>
                <p className="text-gray-600 text-xs indent-4">
                  コメントされた解決案の提案者は、そのコメントを参考にして自身の解決案の編集ができます（これ以外の手段で解決案の編集はできません）。
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 border-2 border-gray-800 text-gray-800 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    5
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">評価期間（提案者間）</h4>
                </div>
                <p className="text-gray-600 text-xs mb-1 indent-4">
                  提案者は、他の提案者の全ての解決案を所定の形式に従って評価します。
                </p>
                <div className="flex items-start gap-0 text-gray-600 text-xs">
                  <span className="font-semibold text-gray-900 select-none shrink-0 leading-snug">＊</span>
                  <p className="m-0 min-w-0 flex-1 indent-4">
                    提案者は、提案期間内に解決案を提出し、かつ、評価期間内に他の提案者の全ての解決案を所定の形式に従って評価することで、
                    <span className="font-medium">提案報酬</span>
                    を受け取れます。
                  </p>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 border-2 border-gray-800 text-gray-800 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    6
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">AI分析</h4>
                </div>
                <p className="text-gray-600 text-xs mb-1 indent-4">
                  投稿者が設定した募集期限の満了後に、AIによって全ての解決案を整理し、その結果を要約します。
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 border-2 border-gray-800 text-gray-800 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    7
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">解決案の採用（投稿者）</h4>
                </div>
                <p className="text-gray-600 text-xs indent-4">
                  投稿者は、課題の解決に最適な解決案を選択します。
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 border-2 border-gray-800 text-gray-800 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    8
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">報酬の支払い</h4>
                </div>
                <p className="text-gray-600 text-xs indent-4 mb-1">
                  提案者のうち、提案期間内に解決案を提出し、かつ、評価期間内に他の提案者の全ての解決案を所定の形式に従って評価した提案者には、ランダム選出のうえで解決案を提案する負担に対する
                  <span className="font-medium">提案報酬</span>
                  が支払われます。
                </p>
                <p className="text-gray-600 text-xs indent-4">
                  また、投稿者が採用した解決案の提案者には、
                  <span className="font-medium">採用報酬</span>
                  が追加で支払われます。
                </p>
                <p className="text-gray-600 text-xs indent-4 mt-2 leading-relaxed bg-amber-50 border border-amber-200 rounded px-2 py-2">
                  {DEMO_REWARD_PAYMENT_NOTICE}
                </p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">注意事項</h3>
            <div
              role="alert"
              className="rounded-lg border-l-4 border-red-600 border-y border-r border-red-200 bg-red-50 px-3 py-3 shadow-sm"
            >
              <p className="text-xs font-medium leading-relaxed text-red-950 indent-4">
                解決案を提案するためには、ランダム選出により選出される必要があるため、時間がかかってしまうおそれがあります。
              </p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">その他の機能</h3>
            <div className="space-y-2">
              <div className="border border-gray-300 rounded p-3">
                <h4 className="font-semibold text-gray-900 text-sm mb-1">通報機能</h4>
                <p className="text-xs text-gray-600 indent-4">
                  課題解決をする上で必要のない内容を含む解決案やコメントを発見した場合、通報することができます。通報数が一定を超えた場合、該当ユーザーの利用を制限または停止することがあります。
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ServiceDescriptionModal;

