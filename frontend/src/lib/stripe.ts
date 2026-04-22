import { loadStripe } from '@stripe/stripe-js';

// Stripeの公開キー（テスト用）
const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || 'pk_test_51234567890abcdef'; // 実際のStripeテストキーに置き換えてください

if (!process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY === 'pk_test_51234567890abcdef') {
  console.warn('⚠️ Stripe公開キーが設定されていません。stripe_setup_guide.mdを参照して実際のキーを設定してください。');
}

export const stripePromise = loadStripe(stripePublishableKey);

// カード要素のオプション
export const cardElementOptions = {
  style: {
    base: {
      fontSize: '16px',
      color: '#424770',
      '::placeholder': {
        color: '#aab7c4',
      },
    },
    invalid: {
      color: '#9e2146',
    },
  },
};
