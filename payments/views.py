"""
報酬・ウォレット管理のビュー
"""
try:
    import stripe
except ImportError:  # デモ版では Stripe SDK を入れない運用を許容
    stripe = None
from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from decimal import Decimal

from .models import Wallet, Payment, PaymentHistory
from .serializers import (
    WalletSerializer, PaymentSerializer, CreatePaymentSerializer,
    WalletBalanceSerializer, PaymentStatsSerializer
)

# Stripe設定
if stripe is not None:
    stripe.api_key = settings.STRIPE_SECRET_KEY

DEMO_STRIPE_DISABLED_MESSAGE = (
    'デモ版のため決済機能（Stripe）は利用できません。'
)


def stripe_disabled_response():
    """デモ版で Stripe API が呼ばれた際の統一レスポンス"""
    return Response(
        {'detail': DEMO_STRIPE_DISABLED_MESSAGE},
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )


class WalletDetailView(generics.RetrieveAPIView):
    """ウォレット詳細取得"""
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet


class PaymentListView(generics.ListAPIView):
    """支払い記録一覧"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(
            Q(payer=user) | Q(recipient=user)
        ).select_related('payer', 'recipient', 'challenge', 'proposal').order_by('-created_at')


class PaymentCreateView(generics.CreateAPIView):
    """支払い作成"""
    serializer_class = CreatePaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # 支払い者を現在のユーザーに設定
        serializer.save(payer=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment(request, payment_id):
    """支払い処理を実行"""
    try:
        payment = get_object_or_404(Payment, id=payment_id, payer=request.user)
        
        # 支払い処理実行
        payment.process_payment()
        
        # 成功時の履歴記録
        PaymentHistory.objects.create(
            payment=payment,
            action='payment_processed',
            details=f'支払いが完了しました: ¥{payment.amount}'
        )
        
        serializer = PaymentSerializer(payment)
        return Response({
            'message': '支払いが完了しました',
            'payment': serializer.data
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_payment(request, payment_id):
    """支払いキャンセル"""
    try:
        payment = get_object_or_404(Payment, id=payment_id, payer=request.user)
        payment.cancel_payment()
        
        # キャンセル時の履歴記録
        PaymentHistory.objects.create(
            payment=payment,
            action='payment_cancelled',
            details=f'支払いがキャンセルされました'
        )
        
        serializer = PaymentSerializer(payment)
        return Response({
            'message': '支払いがキャンセルされました',
            'payment': serializer.data
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_balance(request):
    """ウォレット残高取得"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    serializer = WalletBalanceSerializer({
        'balance': wallet.balance,
        'user_id': request.user.id,
        'username': request.user.username
    })
    
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_stats(request):
    """支払い統計取得"""
    user = request.user
    
    # 支払い統計
    payments_made = Payment.objects.filter(payer=user, status='completed')
    payments_received = Payment.objects.filter(recipient=user, status='completed')
    
    stats = {
        'total_paid': payments_made.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
        'total_received': payments_received.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
        'proposal_rewards_paid': payments_made.filter(payment_type='proposal_reward').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
        'adoption_rewards_paid': payments_made.filter(payment_type='adoption_reward').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
        'proposal_rewards_received': payments_received.filter(payment_type='proposal_reward').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
        'adoption_rewards_received': payments_received.filter(payment_type='adoption_reward').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
    }
    
    serializer = PaymentStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit_money(request):
    """入金処理（テスト用）"""
    amount = request.data.get('amount')
    
    if not amount or amount <= 0:
        return Response({
            'error': '有効な金額を入力してください'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet.deposit(Decimal(str(amount)))
        
        # 入金記録を作成
        payment = Payment.objects.create(
            payer=request.user,
            recipient=request.user,
            amount=Decimal(str(amount)),
            payment_type='deposit',
            status='completed',
            description='入金処理'
        )
        
        return Response({
            'message': f'¥{amount}が入金されました',
            'new_balance': wallet.balance
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """Stripe決済インテント作成"""
    if settings.DEMO_DISABLE_STRIPE:
        return stripe_disabled_response()
    if stripe is None:
        return Response({'error': 'Stripe SDK がインストールされていません'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    amount = request.data.get('amount')
    
    if not amount or amount <= 0:
        return Response({
            'error': '有効な金額を入力してください'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 金額を円単位からセント単位に変換（Stripeはセント単位）
        amount_cents = int(float(amount) * 100)
        
        # PaymentIntentを作成
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='jpy',
            metadata={
                'user_id': str(request.user.id),
                'username': request.user.username
            }
        )
        
        return Response({
            'client_secret': intent.client_secret,
            'publishable_key': settings.STRIPE_PUBLISHABLE_KEY
        })
        
    except stripe.error.StripeError as e:
        return Response({
            'error': f'決済エラー: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'サーバーエラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request):
    """決済完了後の入金処理"""
    if settings.DEMO_DISABLE_STRIPE:
        return stripe_disabled_response()
    if stripe is None:
        return Response({'error': 'Stripe SDK がインストールされていません'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    payment_intent_id = request.data.get('payment_intent_id')
    amount = request.data.get('amount')
    
    if not payment_intent_id or not amount:
        return Response({
            'error': '決済情報が不正です'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # PaymentIntentの状態を確認
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status != 'succeeded':
            return Response({
                'error': '決済が完了していません'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ウォレットに入金
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet.deposit(Decimal(str(amount)))
        
        # 入金記録を作成
        payment = Payment.objects.create(
            payer=request.user,
            recipient=request.user,
            amount=Decimal(str(amount)),
            payment_type='stripe_deposit',
            status='completed',
            description=f'Stripe決済による入金 (PaymentIntent: {payment_intent_id})',
            metadata={'stripe_payment_intent_id': payment_intent_id}
        )
        
        return Response({
            'message': f'¥{amount}が入金されました',
            'new_balance': wallet.balance,
            'payment_id': payment.id
        })
        
    except stripe.error.StripeError as e:
        return Response({
            'error': f'決済確認エラー: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'サーバーエラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stripe_account(request):
    """Stripe Connectアカウント作成（提案者用）"""
    if settings.DEMO_DISABLE_STRIPE:
        return stripe_disabled_response()
    if stripe is None:
        return Response({'error': 'Stripe SDK がインストールされていません'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # 提案者のみ利用可能
        if request.user.user_type != 'proposer':
            return Response({
                'error': '提案者ユーザーのみ利用可能です'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # テスト環境ではモック実装を使用（Connect未有効の場合）
        if settings.DEBUG:
            # テスト用のモックアカウントIDを生成
            mock_account_id = f'acct_test_{request.user.id}_{hash(request.user.email) % 100000}'
            
            # ウォレットにStripeアカウントIDを保存
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet.metadata = wallet.metadata or {}
            wallet.metadata['stripe_connect_account_id'] = mock_account_id
            wallet.metadata['connect_account_status'] = 'completed'  # テスト環境では完了状態
            wallet.save()
            
            return Response({
                'account_id': mock_account_id,
                'onboarding_url': 'http://localhost:3000/profile?success=true',  # テスト用リダイレクト
                'message': 'テスト用Connectアカウントが作成されました（本番環境では実際のStripe Connectが必要です）'
            })
        
        # 本番環境では実際のStripe Connectを使用
        account = stripe.Account.create(
            type='express',
            country='JP',
            email=request.user.email,
            capabilities={
                'card_payments': {'requested': True},
                'transfers': {'requested': True},
            },
            business_type='individual',
        )
        
        # アカウントリンク作成（銀行口座登録用）
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url='http://localhost:3000/profile?refresh=true',
            return_url='http://localhost:3000/profile?success=true',
            type='account_onboarding',
        )
        
        # ウォレットにConnectアカウントIDを保存
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet.metadata = wallet.metadata or {}
        wallet.metadata['stripe_connect_account_id'] = account.id
        wallet.metadata['connect_account_status'] = 'pending'
        wallet.save()
        
        return Response({
            'account_id': account.id,
            'onboarding_url': account_link.url,
            'message': 'Connectアカウントが作成されました。銀行口座情報を登録してください。'
        })
        
    except stripe.error.StripeError as e:
        return Response({
            'error': f'Connectアカウント作成エラー: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'サーバーエラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stripe_account_status(request):
    """Stripe Connectアカウントの状態確認"""
    if settings.DEMO_DISABLE_STRIPE:
        return stripe_disabled_response()
    if stripe is None:
        return Response({'error': 'Stripe SDK がインストールされていません'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # 投稿者と提案者で処理を分岐
        if request.user.user_type == 'contributor':
            # 投稿者：Customer作成
            stripe_customer_id = wallet.metadata.get('stripe_customer_id') if wallet.metadata else None
            
            if not stripe_customer_id:
                return Response({
                    'has_account': False,
                    'account_status': None,
                    'account_type': 'customer'
                })
            
            try:
                customer = stripe.Customer.retrieve(stripe_customer_id)
                return Response({
                    'has_account': True,
                    'customer_id': stripe_customer_id,
                    'account_status': 'completed',
                    'account_type': 'customer'
                })
            except stripe.error.InvalidRequestError:
                wallet.metadata = wallet.metadata or {}
                wallet.metadata['stripe_customer_id'] = None
                wallet.save()
                return Response({
                    'has_account': False,
                    'account_status': None,
                    'account_type': 'customer'
                })
        
        else:  # proposer
            # 提案者：Connectアカウント確認
            connect_account_id = wallet.metadata.get('stripe_connect_account_id') if wallet.metadata else None
            
            if not connect_account_id:
                return Response({
                    'has_account': False,
                    'account_status': None,
                    'account_type': 'connect'
                })
            
            try:
                account = stripe.Account.retrieve(connect_account_id)
                
                # ウォレットのメタデータを更新
                wallet.metadata = wallet.metadata or {}
                wallet.metadata['connect_account_status'] = 'completed' if account.details_submitted else 'pending'
                wallet.save()
                
                return Response({
                    'has_account': True,
                    'account_id': connect_account_id,
                    'account_status': 'completed' if account.details_submitted else 'pending',
                    'account_type': 'connect'
                })
            except stripe.error.InvalidRequestError:
                wallet.metadata = wallet.metadata or {}
                wallet.metadata['stripe_connect_account_id'] = None
                wallet.save()
                return Response({
                    'has_account': False,
                    'account_status': None,
                    'account_type': 'connect'
                })
        
    except stripe.error.StripeError as e:
        return Response({
            'error': f'Stripe状態確認エラー: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'サーバーエラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stripe_customer(request):
    """Stripe Customer作成（投稿者用）"""
    if settings.DEMO_DISABLE_STRIPE:
        return stripe_disabled_response()
    if stripe is None:
        return Response({'error': 'Stripe SDK がインストールされていません'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # 投稿者のみ利用可能
        if request.user.user_type != 'contributor':
            return Response({
                'error': '投稿者ユーザーのみ利用可能です'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Stripe Customerを作成
        customer = stripe.Customer.create(
            email=request.user.email,
            metadata={
                'user_id': str(request.user.id),
                'username': request.user.username,
                'user_type': request.user.user_type,
            }
        )
        
        # ウォレットにStripe Customer IDを保存
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet.metadata = wallet.metadata or {}
        wallet.metadata['stripe_customer_id'] = customer.id
        wallet.metadata['customer_status'] = 'completed'
        wallet.save()
        
        return Response({
            'customer_id': customer.id,
            'message': 'Stripe Customerが作成されました'
        })
        
    except stripe.error.StripeError as e:
        return Response({
            'error': f'Stripe Customer作成エラー: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'サーバーエラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_withdrawal(request):
    """出金申請（提案者ユーザー用）"""
    if settings.DEMO_DISABLE_STRIPE:
        return stripe_disabled_response()
    if stripe is None:
        return Response({'error': 'Stripe SDK がインストールされていません'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.user.user_type != 'proposer':
        return Response({
            'error': '提案者ユーザーのみ利用可能です'
        }, status=status.HTTP_403_FORBIDDEN)
    
    amount = request.data.get('amount')
    
    if not amount or amount <= 0:
        return Response({
            'error': '有効な金額を入力してください'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # 残高チェック
        if wallet.balance < Decimal(str(amount)):
            return Response({
                'error': 'ウォレット残高が不足しています'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Stripeアカウントの確認
        stripe_account_id = wallet.metadata.get('stripe_account_id') if wallet.metadata else None
        if not stripe_account_id:
            return Response({
                'error': 'Stripeアカウントが登録されていません'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Stripeアカウントの状態確認
        account = stripe.Account.retrieve(stripe_account_id)
        if not account.details_submitted:
            return Response({
                'error': 'Stripeアカウントの登録が完了していません'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Transferを作成（Stripeアカウントへの送金）
        transfer = stripe.Transfer.create(
            amount=int(float(amount) * 100),  # 円単位からセント単位に変換
            currency='jpy',
            destination=stripe_account_id,
            metadata={
                'user_id': str(request.user.id),
                'username': request.user.username,
                'withdrawal_type': 'wallet_to_bank'
            }
        )
        
        # ウォレット残高から出金額を減算
        wallet.withdraw(Decimal(str(amount)))
        
        # 出金記録を作成
        payment = Payment.objects.create(
            payer=request.user,
            recipient=request.user,
            amount=Decimal(str(amount)),
            payment_type='withdrawal',
            status='completed',
            description=f'ウォレットから銀行口座への出金 (Transfer: {transfer.id})',
            metadata={'stripe_transfer_id': transfer.id}
        )
        
        return Response({
            'message': f'¥{amount}の出金が完了しました',
            'new_balance': wallet.balance,
            'transfer_id': transfer.id
        })
        
    except stripe.error.StripeError as e:
        return Response({
            'error': f'出金処理エラー: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'サーバーエラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)