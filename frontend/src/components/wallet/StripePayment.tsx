'use client';

import React, { useState } from 'react';
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js';
import { cardElementOptions } from '@/lib/stripe';
import { createPaymentIntent, confirmPayment } from '@/lib/walletAPI';

interface StripePaymentProps {
  amount: number;
  onSuccess: (newBalance: number) => void;
  onError: (error: string) => void;
}

export default function StripePayment({ amount, onSuccess, onError }: StripePaymentProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. PaymentIntentを作成
      const { client_secret } = await createPaymentIntent(amount);
      
      // 2. カード情報を取得
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        throw new Error('カード情報が取得できません');
      }

      // 3. 決済を実行
      const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(client_secret, {
        payment_method: {
          card: cardElement,
        }
      });

      if (stripeError) {
        throw new Error(stripeError.message || '決済に失敗しました');
      }

      if (paymentIntent && paymentIntent.status === 'succeeded') {
        // 4. 決済完了をサーバーに通知
        const result = await confirmPayment(paymentIntent.id, amount);
        onSuccess(result.new_balance);
      } else {
        throw new Error('決済が完了していません');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '決済に失敗しました';
      setError(errorMessage);
      onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="border border-gray-300 rounded-lg p-4">
        <CardElement options={cardElementOptions} />
      </div>
      
      {error && (
        <div className="text-red-600 text-sm">
          {error}
        </div>
      )}
      
      <button
        type="submit"
        disabled={!stripe || loading}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? '処理中...' : `¥${amount.toLocaleString()}を決済`}
      </button>
      
      <div className="text-xs text-gray-500">
        ※ テスト環境では以下のカード番号が使用できます：
        <br />
        カード番号: 4242 4242 4242 4242
        <br />
        有効期限: 任意の未来の日付（例：12/25）
        <br />
        CVC: 任意の3桁（例：123）
      </div>
    </form>
  );
}
