/**
 * ウォレット・報酬管理API
 */
import { tokenManager } from './api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// ウォレット情報
export interface Wallet {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
  };
  balance: number;
  created_at: string;
  updated_at: string;
}

// 支払い記録
export interface Payment {
  id: number;
  payer: {
    id: number;
    username: string;
    email: string;
  };
  recipient: {
    id: number;
    username: string;
    email: string;
  };
  amount: number;
  payment_type: 'proposal_reward' | 'adoption_reward' | 'deposit' | 'withdrawal';
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  challenge?: number;
  proposal?: number;
  description: string;
  history: PaymentHistory[];
  created_at: string;
  updated_at: string;
}

// 支払い履歴
export interface PaymentHistory {
  id: number;
  action: string;
  details: string;
  created_at: string;
}

// 支払い作成リクエスト
export interface CreatePaymentRequest {
  recipient: number;
  amount: number;
  payment_type: 'proposal_reward' | 'adoption_reward';
  challenge?: number;
  proposal?: number;
  description?: string;
}

// 支払い統計
export interface PaymentStats {
  total_paid: number;
  total_received: number;
  proposal_rewards_paid: number;
  adoption_rewards_paid: number;
  proposal_rewards_received: number;
  adoption_rewards_received: number;
}

/**
 * ウォレット情報を取得
 */
export async function getWallet(): Promise<Wallet> {
  const accessToken = tokenManager.getAccessToken();
  console.log('getWallet - accessToken:', accessToken ? 'exists' : 'missing');
  
  const response = await fetch(`${API_BASE_URL}/wallet/wallet/`, {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
  });

  if (!response.ok) {
    throw new Error('ウォレット情報の取得に失敗しました');
  }

  return response.json();
}

/**
 * ウォレット残高を取得
 */
export async function getWalletBalance(): Promise<{ balance: number; user_id: number; username: string }> {
  const accessToken = tokenManager.getAccessToken();
  const response = await fetch(`${API_BASE_URL}/wallet/wallet/balance/`, {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
  });

  if (!response.ok) {
    throw new Error('残高情報の取得に失敗しました');
  }

  return response.json();
}

/**
 * 支払い記録一覧を取得
 */
export async function getPayments(): Promise<Payment[]> {
  const accessToken = tokenManager.getAccessToken();
  const response = await fetch(`${API_BASE_URL}/wallet/payments/`, {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
  });

  if (!response.ok) {
    throw new Error('支払い記録の取得に失敗しました');
  }

  return response.json();
}

/**
 * 支払いを作成
 */
export async function createPayment(paymentData: CreatePaymentRequest): Promise<Payment> {
  const accessToken = tokenManager.getAccessToken();
  const response = await fetch(`${API_BASE_URL}/wallet/payments/create/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
    body: JSON.stringify(paymentData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '支払いの作成に失敗しました');
  }

  return response.json();
}

/**
 * 支払いを処理
 */
export async function processPayment(paymentId: number): Promise<{ message: string; payment: Payment }> {
  const accessToken = tokenManager.getAccessToken();
  const response = await fetch(`${API_BASE_URL}/wallet/payments/${paymentId}/process/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '支払い処理に失敗しました');
  }

  return response.json();
}

/**
 * 支払いをキャンセル
 */
export async function cancelPayment(paymentId: number): Promise<{ message: string; payment: Payment }> {
  const accessToken = tokenManager.getAccessToken();
  const response = await fetch(`${API_BASE_URL}/wallet/payments/${paymentId}/cancel/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '支払いキャンセルに失敗しました');
  }

  return response.json();
}

/**
 * 支払い統計を取得
 */
export async function getPaymentStats(): Promise<PaymentStats> {
  const accessToken = tokenManager.getAccessToken();
  const response = await fetch(`${API_BASE_URL}/wallet/stats/`, {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
  });

  if (!response.ok) {
    throw new Error('支払い統計の取得に失敗しました');
  }

  return response.json();
}

/**
 * 入金処理（テスト用）
 */
export async function depositMoney(amount: number): Promise<{ message: string; new_balance: number }> {
  const accessToken = tokenManager.getAccessToken();
  const response = await fetch(`${API_BASE_URL}/wallet/wallet/deposit/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
    body: JSON.stringify({ amount }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '入金処理に失敗しました');
  }

  return response.json();
}

/**
 * Stripe決済インテント作成
 */
export async function createPaymentIntent(amount: number): Promise<{ client_secret: string; publishable_key: string }> {
  const accessToken = tokenManager.getAccessToken();
  
  const response = await fetch(`${API_BASE_URL}/wallet/stripe/create-payment-intent/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
    body: JSON.stringify({ amount }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '決済インテントの作成に失敗しました');
  }

  return response.json();
}

/**
 * Stripe決済確認
 */
export async function confirmPayment(paymentIntentId: string, amount: number): Promise<{ message: string; new_balance: number; payment_id: number }> {
  const accessToken = tokenManager.getAccessToken();
  
  const response = await fetch(`${API_BASE_URL}/wallet/stripe/confirm-payment/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
    body: JSON.stringify({ 
      payment_intent_id: paymentIntentId,
      amount: amount 
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '決済確認に失敗しました');
  }

  return response.json();
}

/**
 * Stripe Customer作成（投稿者ユーザー用）
 */
export async function createStripeCustomer(): Promise<{ customer_id: string; message: string }> {
  const accessToken = tokenManager.getAccessToken();
  
  if (!accessToken) {
    throw new Error('認証が必要です。ログインし直してください。');
  }
  
  const response = await fetch(`${API_BASE_URL}/wallet/stripe/create-customer/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      try {
        const errorData = await response.json();
        throw new Error(errorData.error || errorData.detail || 'Stripe Customer作成に失敗しました');
      } catch {
        throw new Error(`サーバーエラー (${response.status}): ${response.statusText}`);
      }
    } else {
      if (response.status === 401) {
        throw new Error('認証が無効です。ログインし直してください。');
      } else if (response.status === 500) {
        throw new Error('サーバーエラーが発生しました。管理者にお問い合わせください。');
      } else {
        throw new Error(`サーバーエラー (${response.status}): ${response.statusText}`);
      }
    }
  }

  try {
    return await response.json();
  } catch {
    throw new Error('サーバーからの応答が無効です');
  }
}

/**
 * Stripe Connectアカウント作成（提案者ユーザー用）
 */
export async function createStripeAccount(): Promise<{ account_id: string; onboarding_url: string; message: string }> {
  const accessToken = tokenManager.getAccessToken();
  
  if (!accessToken) {
    throw new Error('認証が必要です。ログインし直してください。');
  }
  
  const response = await fetch(`${API_BASE_URL}/wallet/stripe/create-account/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    // レスポンスがJSONかどうか確認
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      try {
        const errorData = await response.json();
        throw new Error(errorData.error || errorData.detail || 'Stripeアカウント作成に失敗しました');
      } catch {
        throw new Error(`サーバーエラー (${response.status}): ${response.statusText}`);
      }
    } else {
      // HTMLエラーページが返された場合
      if (response.status === 401) {
        throw new Error('認証が無効です。ログインし直してください。');
      } else if (response.status === 500) {
        throw new Error('サーバーエラーが発生しました。管理者にお問い合わせください。');
      } else {
        throw new Error(`サーバーエラー (${response.status}): ${response.statusText}`);
      }
    }
  }

  try {
    return await response.json();
  } catch {
    throw new Error('サーバーからの応答が無効です');
  }
}

/**
 * Stripeアカウント状態確認
 */
export async function getStripeAccountStatus(): Promise<{ has_account: boolean; account_status: string | null; account_id?: string }> {
  const accessToken = tokenManager.getAccessToken();
  
  if (!accessToken) {
    // 認証トークンがない場合は未登録として返す
    return { has_account: false, account_status: null };
  }
  
  const response = await fetch(`${API_BASE_URL}/wallet/stripe/account-status/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    // レスポンスがJSONかどうか確認
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      try {
        const errorData = await response.json();
        if (response.status === 401) {
          return { has_account: false, account_status: null };
        }
        throw new Error(errorData.error || errorData.detail || 'Stripeアカウント状態確認に失敗しました');
      } catch {
        return { has_account: false, account_status: null };
      }
    } else {
      // HTMLエラーページが返された場合
      return { has_account: false, account_status: null };
    }
  }

  try {
    return await response.json();
  } catch {
    return { has_account: false, account_status: null };
  }
}

/**
 * 出金申請（提案者ユーザー用）
 */
export async function createWithdrawal(amount: number): Promise<{ message: string; new_balance: number; transfer_id: string }> {
  const accessToken = tokenManager.getAccessToken();
  
  const response = await fetch(`${API_BASE_URL}/wallet/withdraw/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
    body: JSON.stringify({ amount }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '出金処理に失敗しました');
  }

  return response.json();
}
