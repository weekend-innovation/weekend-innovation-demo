'use client';

import React from 'react';
import { openServiceDescriptionModal } from '@/lib/openServiceDescription';

export type DemoVersionRole = 'contributor' | 'proposer';

export const DEMO_REWARD_PAYMENT_NOTICE =
  'デモ版では、提案報酬・採用報酬の支払い・受け取りは行いません。';

type DemoVersionNoticeBodyProps = {
  onOpenServiceDescription?: () => void;
};

export function DemoVersionNoticeBody({ onOpenServiceDescription }: DemoVersionNoticeBodyProps) {
  return (
    <>
      <p className="text-sm text-amber-900/90 leading-relaxed indent-4">{DEMO_REWARD_PAYMENT_NOTICE}</p>
      <p className="text-sm text-amber-900/90 leading-relaxed mt-3 indent-4">
        報酬の扱いの詳細は、
        {onOpenServiceDescription ? (
          <button
            type="button"
            onClick={onOpenServiceDescription}
            className="font-semibold text-amber-950 underline underline-offset-2 hover:text-amber-800 cursor-pointer"
          >
            サービスの説明
          </button>
        ) : (
          <span className="font-semibold text-amber-950">サービスの説明</span>
        )}
        にてご確認ください。
      </p>
    </>
  );
}

type ModalProps = {
  isOpen: boolean;
  onClose: () => void;
  role?: DemoVersionRole;
};

function handleOpenServiceFromDemo(onClose: () => void) {
  onClose();
  queueMicrotask(() => openServiceDescriptionModal());
}

export function DemoVersionModal({ isOpen, onClose, role }: ModalProps) {
  if (!isOpen) return null;
  void role;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-300 shadow-lg"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="demo-version-modal-title"
      >
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <h2 id="demo-version-modal-title" className="text-xl font-bold text-gray-900">
            デモ版について
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl cursor-pointer leading-none"
            aria-label="閉じる"
          >
            ✕
          </button>
        </div>
        <div className="px-6 py-6">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <DemoVersionNoticeBody
              onOpenServiceDescription={() => handleOpenServiceFromDemo(onClose)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export function DashboardDemoVersionTrigger({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="inline-block relative">
      <span className="text-2xl font-bold text-amber-900">【デモ版】</span>
      <button
        type="button"
        onClick={onOpen}
        className="absolute -top-1 -right-5 w-4 h-4 border border-gray-400 text-gray-600 rounded-full hover:border-gray-600 hover:text-gray-800 transition-colors duration-200 flex items-center justify-center text-xs font-bold cursor-pointer"
        title="デモ版について"
        aria-label="デモ版についてを表示"
      >
        ?
      </button>
    </div>
  );
}

