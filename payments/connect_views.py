"""
Stripe Connect実装例（手数料収益モデル用）
"""
import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_connect_account(request):
    """提案者用Connectアカウント作成"""
    try:
        # 提案者のみ利用可能
        if request.user.user_type != 'proposer':
            return Response({
                'error': '提案者ユーザーのみ利用可能です'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Expressアカウント作成（簡単なセットアップ）
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_reward_payment(request):
    """報酬支払い処理（投稿者→提案者、手数料付き）"""
    try:
        challenge_id = request.data.get('challenge_id')
        proposal_id = request.data.get('proposal_id')
        amount = Decimal(str(request.data.get('amount')))
        payment_type = request.data.get('payment_type')  # 'proposal_reward' or 'adoption_reward'
        
        # 手数料計算（例：10%）
        platform_fee_rate = Decimal('0.10')  # 10%
        platform_fee = amount * platform_fee_rate
        proposer_amount = amount - platform_fee
        
        # 提案者のConnectアカウントIDを取得
        proposer = Proposal.objects.get(id=proposal_id).proposer
        proposer_wallet = Wallet.objects.get(user=proposer)
        connect_account_id = proposer_wallet.metadata.get('stripe_connect_account_id')
        
        if not connect_account_id:
            return Response({
                'error': '提案者のConnectアカウントが登録されていません'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 投稿者のクレジットカードで決済
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # セント単位
            currency='jpy',
            customer=request.user.stripe_customer_id,
            application_fee_amount=int(platform_fee * 100),  # プラットフォーム手数料
            transfer_data={
                'destination': connect_account_id,  # 提案者のConnectアカウント
            },
            metadata={
                'challenge_id': challenge_id,
                'proposal_id': proposal_id,
                'payment_type': payment_type,
                'platform_fee': str(platform_fee),
                'proposer_amount': str(proposer_amount),
            }
        )
        
        return Response({
            'payment_intent_id': payment_intent.id,
            'client_secret': payment_intent.client_secret,
            'amount': str(amount),
            'platform_fee': str(platform_fee),
            'proposer_amount': str(proposer_amount),
        })
        
    except Exception as e:
        return Response({
            'error': f'決済処理エラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """投稿者用決済インテント作成（カード情報不要）"""
    try:
        amount = Decimal(str(request.data.get('amount')))
        
        # 投稿者のみ利用可能
        if request.user.user_type != 'contributor':
            return Response({
                'error': '投稿者ユーザーのみ利用可能です'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Customer作成（初回のみ）
        if not hasattr(request.user, 'stripe_customer_id'):
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={
                    'user_id': str(request.user.id),
                    'username': request.user.username,
                }
            )
            # Customer IDを保存
            request.user.stripe_customer_id = customer.id
            request.user.save()
        
        # PaymentIntent作成
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # セント単位
            currency='jpy',
            customer=request.user.stripe_customer_id,
            metadata={
                'user_id': str(request.user.id),
                'payment_type': 'wallet_topup',
            }
        )
        
        return Response({
            'client_secret': payment_intent.client_secret,
            'amount': str(amount),
        })
        
    except Exception as e:
        return Response({
            'error': f'決済インテント作成エラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_platform_earnings(request):
    """プラットフォーム収益確認（管理者用）"""
    try:
        # 管理者のみアクセス可能
        if not request.user.is_staff:
            return Response({
                'error': '管理者のみアクセス可能です'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 過去30日の手数料収益を計算
        # （実際の実装ではデータベースから集計）
        
        return Response({
            'total_platform_fees': '50000',  # 例：5万円
            'transaction_count': 150,
            'average_fee_rate': '10%',
        })
        
    except Exception as e:
        return Response({
            'error': f'収益データ取得エラー: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
