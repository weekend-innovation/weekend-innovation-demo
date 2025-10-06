/**
 * ウォレット管理ページ
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Elements } from '@stripe/react-stripe-js';
import { stripePromise } from '../../lib/stripe';
import StripePayment from '../../components/wallet/StripePayment';
import { 
  getWallet, 
  getPayments, 
  getPaymentStats, 
  depositMoney,
  getStripeAccountStatus,
  createWithdrawal,
  type Wallet, 
  type Payment, 
  type PaymentStats 
} from '../../lib/walletAPI';

const WalletPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [stats, setStats] = useState<PaymentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [depositAmount, setDepositAmount] = useState<number>(0);
  const [depositing, setDepositing] = useState(false);
  const [showStripePayment, setShowStripePayment] = useState(false);
  const [withdrawalAmount, setWithdrawalAmount] = useState<number>(0);
  const [withdrawing, setWithdrawing] = useState(false);
  const [stripeAccountStatus, setStripeAccountStatus] = useState<{
    has_account: boolean;
    account_status: string | null;
    account_id?: string;
  } | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    fetchWalletData();
  }, [isAuthenticated, router]);

  const fetchWalletData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 認証トークンを確認
      const token = localStorage.getItem('access_token');
      console.log('Access token:', token ? 'exists' : 'missing');
      console.log('User:', user);

      const [walletData, paymentsData, statsData] = await Promise.all([
        getWallet(),
        getPayments(),
        getPaymentStats()
      ]);

      console.log('Payments data:', paymentsData);
      console.log('Payments type:', typeof paymentsData);
      console.log('Is array:', Array.isArray(paymentsData));

      setWallet(walletData);
      
      // ページネーション対応: results配列を取得
      if (paymentsData && paymentsData.results && Array.isArray(paymentsData.results)) {
        setPayments(paymentsData.results);
      } else if (Array.isArray(paymentsData)) {
        setPayments(paymentsData);
      } else {
        console.error('Payments data format is unexpected:', paymentsData);
        setPayments([]);
      }
      
      setStats(statsData);
      
      // 全ユーザーでStripeアカウント状態を取得
      try {
        const stripeStatus = await getStripeAccountStatus();
        setStripeAccountStatus(stripeStatus);
      } catch (stripeErr) {
        console.error('Stripeアカウント状態取得エラー:', stripeErr);
        // Stripeエラーは無視（ウォレット表示は継続）
      }
    } catch (err) {
      console.error('ウォレットデータ取得エラー:', err);
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleDeposit = async () => {
    if (depositAmount <= 0) {
      alert('有効な金額を入力してください');
      return;
    }

    try {
      setDepositing(true);
      const result = await depositMoney(depositAmount);
      alert(result.message);
      setDepositAmount(0);
      await fetchWalletData(); // データを再取得
    } catch (err) {
      console.error('入金エラー:', err);
      alert(err instanceof Error ? err.message : '入金処理に失敗しました');
    } finally {
      setDepositing(false);
    }
  };

  const handleStripeSuccess = (newBalance: number) => {
    alert(`決済が完了しました！新しい残高: ¥${newBalance.toLocaleString()}`);
    setShowStripePayment(false);
    setDepositAmount(0);
    // ウォレット情報を再取得
    fetchWalletData();
  };

  const handleStripeError = (error: string) => {
    alert(`決済エラー: ${error}`);
  };

  const handleWithdrawal = async () => {
    if (withdrawalAmount <= 0) {
      alert('有効な金額を入力してください');
      return;
    }

    if (!wallet || wallet.balance < withdrawalAmount) {
      alert('ウォレット残高が不足しています');
      return;
    }

    if (!stripeAccountStatus?.has_account || stripeAccountStatus.account_status !== 'completed') {
      alert('Stripeアカウントの登録が完了していません');
      return;
    }

    setWithdrawing(true);
    try {
      const result = await createWithdrawal(withdrawalAmount);
      alert(result.message);
      setWithdrawalAmount(0);
      // ウォレット情報を再取得
      await fetchWalletData();
    } catch (err) {
      console.error('出金エラー:', err);
      alert(err instanceof Error ? err.message : '出金処理に失敗しました');
    } finally {
      setWithdrawing(false);
    }
  };

  const formatCurrency = (amount: number): string => {
    return `¥${amount.toLocaleString()}`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('ja-JP');
  };

  const getPaymentTypeLabel = (type: string): string => {
    const labels = {
      'proposal_reward': '提案報酬',
      'adoption_reward': '採用報酬',
      'deposit': '入金',
      'withdrawal': '出金'
    };
    return labels[type as keyof typeof labels] || type;
  };

  const getStatusLabel = (status: string): string => {
    const labels = {
      'pending': '処理中',
      'completed': '完了',
      'failed': '失敗',
      'cancelled': 'キャンセル'
    };
    return labels[status as keyof typeof labels] || status;
  };

  const getStatusColor = (status: string): string => {
    const colors = {
      'pending': 'text-yellow-600 bg-yellow-100',
      'completed': 'text-green-600 bg-green-100',
      'failed': 'text-red-600 bg-red-100',
      'cancelled': 'text-gray-600 bg-gray-100'
    };
    return colors[status as keyof typeof colors] || 'text-gray-600 bg-gray-100';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchWalletData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            再試行
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">ウォレット管理</h1>
          <p className="mt-2 text-gray-600">
            {user?.user_type === 'contributor' 
              ? '報酬の支払いを管理できます' 
              : '報酬の受取を管理できます'
            }
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* ウォレット情報 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">ウォレット残高</h2>
              <div className="text-3xl font-bold text-blue-600 mb-4">
                {wallet ? formatCurrency(wallet.balance) : '¥0'}
              </div>
              
              {/* 投稿者ユーザー向けの説明 */}
              {user?.user_type === 'contributor' && (
                <div className="space-y-3 mb-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm text-blue-800">
                      この残高は、課題への提案・採用報酬の支払いに使用されます。
                    </p>
                  </div>
                  
                  {/* Stripeアカウント状態 */}
                  {stripeAccountStatus && (
                    <div className={`border rounded-lg p-3 ${
                      stripeAccountStatus.has_account && stripeAccountStatus.account_status === 'completed'
                        ? 'bg-green-50 border-green-200'
                        : 'bg-yellow-50 border-yellow-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-3 h-3 rounded-full ${
                          stripeAccountStatus.has_account && stripeAccountStatus.account_status === 'completed'
                            ? 'bg-green-500'
                            : 'bg-yellow-500'
                        }`}></div>
                        <span className="text-sm font-medium">
                          {stripeAccountStatus.has_account ? (
                            stripeAccountStatus.account_status === 'completed' ? '決済可能' : '登録中'
                          ) : '未登録'}
                        </span>
                      </div>
                      <p className={`text-sm ${
                        stripeAccountStatus.has_account && stripeAccountStatus.account_status === 'completed'
                          ? 'text-green-700'
                          : 'text-yellow-700'
                      }`}>
                        {stripeAccountStatus.has_account ? (
                          stripeAccountStatus.account_status === 'completed' 
                            ? 'クレジットカード決済が可能です'
                            : 'プロフィールページで登録手続きを完了してください'
                        ) : 'ウォレット機能を利用するにはプロフィールページでStripeアカウントの登録が必要です'}
                      </p>
                    </div>
                  )}
                </div>
              )}
              
              {/* 提案者ユーザー向けの説明 */}
              {user?.user_type === 'proposer' && (
                <div className="space-y-3 mb-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm text-blue-800">
                      この残高は、あなたの解決案が選出・採用された際に自動的に加算された報酬です。
                    </p>
                  </div>
                  
                  {/* Stripeアカウント状態 */}
                  {stripeAccountStatus && (
                    <div className={`border rounded-lg p-3 ${
                      stripeAccountStatus.has_account && stripeAccountStatus.account_status === 'completed'
                        ? 'bg-green-50 border-green-200'
                        : 'bg-yellow-50 border-yellow-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-3 h-3 rounded-full ${
                          stripeAccountStatus.has_account && stripeAccountStatus.account_status === 'completed'
                            ? 'bg-green-500'
                            : 'bg-yellow-500'
                        }`}></div>
                        <span className="text-sm font-medium">
                          {stripeAccountStatus.has_account ? (
                            stripeAccountStatus.account_status === 'completed' ? '出金可能' : '登録中'
                          ) : '未登録'}
                        </span>
                      </div>
                      <p className={`text-sm ${
                        stripeAccountStatus.has_account && stripeAccountStatus.account_status === 'completed'
                          ? 'text-green-700'
                          : 'text-yellow-700'
                      }`}>
                        {stripeAccountStatus.has_account ? (
                          stripeAccountStatus.account_status === 'completed' 
                            ? '銀行口座への出金が可能です'
                            : 'プロフィールページで登録手続きを完了してください'
                        ) : '報酬を受け取るにはプロフィールページでStripeアカウントの登録が必要です'}
                      </p>
                    </div>
                  )}
                  
                  {/* 出金機能（Stripeアカウント登録済みの場合のみ） */}
                  {stripeAccountStatus?.has_account && stripeAccountStatus.account_status === 'completed' && wallet && wallet.balance > 0 && (
                    <div className="border-t pt-4">
                      <h3 className="text-sm font-medium text-gray-700 mb-2">出金</h3>
                      <div className="space-y-3">
                        <div className="flex gap-2">
                          <input
                            type="number"
                            value={withdrawalAmount}
                            onChange={(e) => setWithdrawalAmount(Number(e.target.value))}
                            placeholder="出金額"
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="1"
                            max={wallet.balance}
                          />
                          <button
                            onClick={handleWithdrawal}
                            disabled={withdrawing || withdrawalAmount <= 0 || withdrawalAmount > wallet.balance}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {withdrawing ? '出金中...' : '出金'}
                          </button>
                        </div>
                        <p className="text-xs text-gray-500">
                          出金は銀行口座に反映されるまで1-3営業日かかる場合があります
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {/* 投稿者ユーザーのみ入金機能を表示（Stripe登録済みの場合のみ） */}
              {user?.user_type === 'contributor' && stripeAccountStatus?.has_account && stripeAccountStatus.account_status === 'completed' && (
                <div className="border-t pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">入金</h3>
                  
                  {!showStripePayment ? (
                    <div className="space-y-3">
                      <div className="flex gap-2">
                        <input
                          type="number"
                          value={depositAmount}
                          onChange={(e) => setDepositAmount(Number(e.target.value))}
                          placeholder="金額"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          min="1"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleDeposit}
                          disabled={depositing || depositAmount <= 0}
                          className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {depositing ? '入金中...' : 'テスト入金'}
                        </button>
                        <button
                          onClick={() => setShowStripePayment(true)}
                          disabled={depositing || depositAmount <= 0}
                          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          クレジットカード決済
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">決済金額: ¥{depositAmount.toLocaleString()}</span>
                        <button
                          onClick={() => setShowStripePayment(false)}
                          className="text-sm text-gray-500 hover:text-gray-700"
                        >
                          キャンセル
                        </button>
                      </div>
                      <Elements stripe={stripePromise}>
                        <StripePayment
                          amount={depositAmount}
                          onSuccess={handleStripeSuccess}
                          onError={handleStripeError}
                        />
                      </Elements>
                    </div>
                  )}
                </div>
              )}
              
            </div>

            {/* 統計情報 */}
            {stats && (
              <div className="bg-white rounded-lg shadow-sm p-6 mt-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">統計情報</h2>
                <div className="space-y-3">
                  {user?.user_type === 'contributor' ? (
                    // 投稿者ユーザーの表示
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-600">総支払い額</span>
                        <span className="font-medium">{formatCurrency(stats.total_paid)}</span>
                      </div>
                      <div className="border-t pt-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">提案報酬（支払い）</span>
                          <span>{formatCurrency(stats.proposal_rewards_paid)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">採用報酬（支払い）</span>
                          <span>{formatCurrency(stats.adoption_rewards_paid)}</span>
                        </div>
                      </div>
                    </>
                  ) : (
                    // 提案者ユーザーの表示
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-600">総受取額</span>
                        <span className="font-medium text-green-600">{formatCurrency(stats.total_received)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">総支払い額</span>
                        <span className="font-medium">{formatCurrency(stats.total_paid)}</span>
                      </div>
                      <div className="border-t pt-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">提案報酬（受取）</span>
                          <span className="text-green-600">{formatCurrency(stats.proposal_rewards_received)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">採用報酬（受取）</span>
                          <span className="text-green-600">{formatCurrency(stats.adoption_rewards_received)}</span>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 支払い記録 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {user?.user_type === 'contributor' ? '支払い記録' : '受取記録'}
              </h2>
              
              {!Array.isArray(payments) || payments.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  {user?.user_type === 'contributor' ? '支払い記録がありません' : '受取記録がありません'}
                </p>
              ) : (
                <div className="space-y-4">
                  {payments.map((payment) => (
                    <div key={payment.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-medium text-gray-900">
                            {payment.payer.username} → {payment.recipient.username}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {getPaymentTypeLabel(payment.payment_type)}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-semibold text-gray-900">
                            {formatCurrency(payment.amount)}
                          </div>
                          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(payment.status)}`}>
                            {getStatusLabel(payment.status)}
                          </span>
                        </div>
                      </div>
                      
                      {payment.description && (
                        <p className="text-sm text-gray-600 mb-2">{payment.description}</p>
                      )}
                      
                      <p className="text-xs text-gray-500">
                        {formatDate(payment.created_at)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WalletPage;
