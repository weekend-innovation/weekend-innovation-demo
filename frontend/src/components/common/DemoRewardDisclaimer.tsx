'use client';

import React from 'react';

type DemoRewardAmountPlaceholderProps = {
  className?: string;
};

/**
 * デモ版では金額を表示しないため、共通プレースホルダを表示する。
 */
export function DemoRewardAmountPlaceholder({ className = '' }: DemoRewardAmountPlaceholderProps) {
  return <span className={className}>--万円</span>;
}

