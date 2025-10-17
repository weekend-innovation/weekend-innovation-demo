# Weekend Innovation 実装例

## データベースモデル

### 1. ユーザー認証・プロフィール

```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPES = [
        ('contributor', '投稿者'),
        ('proposer', '提案者'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ContributorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100, verbose_name="商号")
    representative_name = models.CharField(max_length=50, verbose_name="代表者名")
    address = models.TextField(verbose_name="住所")
    phone_number = models.CharField(max_length=20, verbose_name="電話番号")
    email = models.EmailField(verbose_name="メールアドレス")
    industry = models.CharField(max_length=50, verbose_name="業種")
    employee_count = models.IntegerField(null=True, blank=True, verbose_name="従業員数")
    established_year = models.IntegerField(null=True, blank=True, verbose_name="設立年")
    company_url = models.URLField(null=True, blank=True, verbose_name="会社URL")
    company_logo = models.ImageField(upload_to='company_logos/', null=True, blank=True, verbose_name="会社ロゴ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ProposerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50, verbose_name="氏名")
    gender = models.CharField(max_length=10, choices=[('male', '男性'), ('female', '女性'), ('other', 'その他')], verbose_name="性別")
    birth_date = models.DateField(verbose_name="生年月日")
    address = models.TextField(verbose_name="住所")
    phone_number = models.CharField(max_length=20, verbose_name="電話番号")
    email = models.EmailField(verbose_name="メールアドレス")
    occupation = models.CharField(max_length=50, null=True, blank=True, verbose_name="職業")
    expertise = models.CharField(max_length=100, null=True, blank=True, verbose_name="専門分野")
    bio = models.TextField(null=True, blank=True, verbose_name="自己紹介")
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True, verbose_name="プロフィール画像")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2. 課題管理

```python
# challenges/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Challenge(models.Model):
    STATUS_CHOICES = [
        ('open', '募集中'),
        ('closed', '締切'),
        ('completed', '完了'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="課題タイトル")
    description = models.TextField(verbose_name="課題内容")
    contributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributed_challenges')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="提案報酬")
    adoption_reward = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="採用報酬")
    required_participants = models.IntegerField(verbose_name="選出人数")
    deadline = models.DateTimeField(verbose_name="期限")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
```

### 3. 提案管理

```python
# proposals/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Proposal(models.Model):
    challenge = models.ForeignKey('challenges.Challenge', on_delete=models.CASCADE, related_name='proposals')
    proposer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposals')
    conclusion = models.TextField(verbose_name="結論")
    reasoning = models.TextField(verbose_name="理由")
    is_adopted = models.BooleanField(default=False, verbose_name="採用フラグ")
    is_deleted = models.BooleanField(default=False, verbose_name="削除フラグ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class ProposalComment(models.Model):
    COMMENT_TARGETS = [
        ('reasoning', '理由'),
        ('inference', '推論過程'),
    ]
    
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_comments')
    target_section = models.CharField(max_length=20, choices=COMMENT_TARGETS, verbose_name="コメント対象")
    conclusion = models.TextField(verbose_name="コメントの結論")
    reasoning = models.TextField(verbose_name="コメントの理由")
    is_deleted = models.BooleanField(default=False, verbose_name="削除フラグ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']

class ProposalEvaluation(models.Model):
    EVALUATION_CHOICES = [
        ('yes', 'Yes'),
        ('maybe', 'Maybe'),
        ('no', 'No'),
    ]
    
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='evaluations')
    evaluator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_evaluations')
    evaluation = models.CharField(max_length=10, choices=EVALUATION_CHOICES, verbose_name="評価")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['proposal', 'evaluator']
```

### 4. 選出機能

```python
# selection/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Selection(models.Model):
    challenge = models.ForeignKey('challenges.Challenge', on_delete=models.CASCADE, related_name='selections')
    proposer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='selections')
    selected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['challenge', 'proposer']
```

### 5. 報酬管理

```python
# payments/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="残高")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Payment(models.Model):
    PAYMENT_TYPES = [
        ('proposal', '提案報酬'),
        ('adoption', '採用報酬'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_payments')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="金額")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, verbose_name="支払いタイプ")
    challenge = models.ForeignKey('challenges.Challenge', on_delete=models.CASCADE, related_name='payments')
    proposal = models.ForeignKey('proposals.Proposal', on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    status = models.CharField(max_length=20, default='pending', verbose_name="ステータス")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

### 6. 報告・モデレーション

```python
# moderation/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Report(models.Model):
    REPORT_TYPES = [
        ('proposal', '提案'),
        ('comment', 'コメント'),
    ]
    
    REPORT_REASONS = [
        ('harassment', '誹謗中傷'),
        ('spam', 'スパム'),
        ('inappropriate', '不適切な内容'),
        ('off_topic', 'トピック外'),
        ('other', 'その他'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="報告タイプ")
    report_reason = models.CharField(max_length=20, choices=REPORT_REASONS, verbose_name="報告理由")
    description = models.TextField(verbose_name="報告詳細")
    proposal = models.ForeignKey('proposals.Proposal', on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    comment = models.ForeignKey('proposals.ProposalComment', on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    is_resolved = models.BooleanField(default=False, verbose_name="解決フラグ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class UserSuspension(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suspensions')
    reason = models.TextField(verbose_name="利用停止理由")
    suspension_start = models.DateTimeField(verbose_name="利用停止開始日時")
    suspension_end = models.DateTimeField(verbose_name="利用停止終了日時")
    is_active = models.BooleanField(default=True, verbose_name="アクティブフラグ")
    created_at = models.DateTimeField(auto_now_add=True)
```

### 7. 通知管理
[Fast Refresh] rebuilding
C:\Users\steph\dev\src\client\dev\report-hmr-latency.ts:26 [Fast Refresh] done in 984ms
C:\Users\steph\dev\python_app\mvp_project\frontend\src\lib\proposalAPI.ts:41   GET http://localhost:8000/api/proposals/ 401 (Unauthorized)
apiCall @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\lib\proposalAPI.ts:41
getProposals @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\lib\proposalAPI.ts:68
fetchDashboardData @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:29
ProposerDashboard.useEffect @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:50
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23668
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
commitHookEffectListMount @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:12344
commitHookPassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:12465
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14562
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
doubleInvokeEffectsOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16565
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16529
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
commitDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16574
flushPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16347
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15973
performWorkUntilDeadline @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\scheduler\cjs\scheduler.development.js:45
<ProposerDashboard>
exports.jsx @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-runtime.development.js:323
ClientPageRoot @ C:\Users\steph\dev\src\client\components\client-page.tsx:60
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10806
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopConcurrentByScheduler @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15720
renderRootConcurrent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15695
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14989
performWorkOnRootViaSchedulerTask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16815
performWorkUntilDeadline @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\scheduler\cjs\scheduler.development.js:45
"use client"
Function.all @ VM496 <anonymous>:1
Function.all @ VM496 <anonymous>:1
initializeElement @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1343
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3066
initializeModelChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1246
resolveModelChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1101
processFullStringRow @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2899
processFullBinaryRow @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2766
processBinaryChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2969
progress @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3233
"use server"
ResponseInstance @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2041
createResponseFromOptions @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3094
exports.createFromReadableStream @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3478
createFromNextReadableStream @ C:\Users\steph\src\client\components\router-reducer\fetch-server-response.ts:388
fetchServerResponse @ C:\Users\steph\src\client\components\router-reducer\fetch-server-response.ts:216
await in fetchServerResponse
eval @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:323
task @ C:\Users\steph\dev\src\client\components\promise-queue.ts:33
processNext @ C:\Users\steph\dev\src\client\components\promise-queue.ts:66
enqueue @ C:\Users\steph\dev\src\client\components\promise-queue.ts:46
createLazyPrefetchEntry @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:322
getOrCreatePrefetchCacheEntry @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:227
navigateReducer @ C:\Users\src\client\components\router-reducer\reducers\navigate-reducer.ts:216
clientReducer @ C:\Users\steph\src\client\components\router-reducer\router-reducer.ts:32
action @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:221
runAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:108
dispatchAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:173
dispatch @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:219
eval @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:45
startTransition @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:7967
dispatch @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:44
dispatchAppRouterAction @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:22
dispatchNavigateAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:290
eval @ C:\Users\steph\dev\src\client\app-dir\link.tsx:292
exports.startTransition @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react.development.js:1148
linkClicked @ C:\Users\steph\dev\src\client\app-dir\link.tsx:291
onClick @ C:\Users\steph\dev\src\client\app-dir\link.tsx:639
executeDispatch @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16970
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
processDispatchQueue @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17020
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17621
batchedUpdates$1 @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:3311
dispatchEventForPluginEventSystem @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17174
dispatchEvent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:21357
dispatchDiscreteEvent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:21325
<a>
exports.jsx @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-runtime.development.js:323
LinkComponent @ C:\Users\steph\dev\src\client\app-dir\link.tsx:726
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10857
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15546
renderRootSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15526
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14990
performSyncWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16830
flushSyncWorkAcrossRoots_impl @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16676
processRootScheduleInMicrotask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16714
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16849
<LinkComponent>
exports.jsxDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-dev-runtime.development.js:323
Header @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\components\layout\Header.tsx:189
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10857
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15546
renderRootSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15526
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14990
performSyncWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16830
flushSyncWorkAcrossRoots_impl @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16676
processRootScheduleInMicrotask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16714
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16849
C:\Users\steph\dev\python_app\mvp_project\frontend\src\lib\proposalAPI.ts:41   GET http://localhost:8000/api/proposals/ 401 (Unauthorized)
apiCall @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\lib\proposalAPI.ts:41
getProposals @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\lib\proposalAPI.ts:68
fetchDashboardData @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:29
ProposerDashboard.useEffect @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:50
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23668
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
commitHookEffectListMount @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:12344
commitHookPassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:12465
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14386
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14398
flushPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16337
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15973
performWorkUntilDeadline @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\scheduler\cjs\scheduler.development.js:45
<ProposerDashboard>
exports.jsx @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-runtime.development.js:323
ClientPageRoot @ C:\Users\steph\dev\src\client\components\client-page.tsx:60
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10806
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopConcurrentByScheduler @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15720
renderRootConcurrent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15695
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14989
performWorkOnRootViaSchedulerTask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16815
performWorkUntilDeadline @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\scheduler\cjs\scheduler.development.js:45
"use client"
Function.all @ VM496 <anonymous>:1
Function.all @ VM496 <anonymous>:1
initializeElement @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1343
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3066
initializeModelChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1246
resolveModelChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1101
processFullStringRow @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2899
processFullBinaryRow @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2766
processBinaryChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2969
progress @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3233
"use server"
ResponseInstance @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2041
createResponseFromOptions @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3094
exports.createFromReadableStream @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3478
createFromNextReadableStream @ C:\Users\steph\src\client\components\router-reducer\fetch-server-response.ts:388
fetchServerResponse @ C:\Users\steph\src\client\components\router-reducer\fetch-server-response.ts:216
await in fetchServerResponse
eval @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:323
task @ C:\Users\steph\dev\src\client\components\promise-queue.ts:33
processNext @ C:\Users\steph\dev\src\client\components\promise-queue.ts:66
enqueue @ C:\Users\steph\dev\src\client\components\promise-queue.ts:46
createLazyPrefetchEntry @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:322
getOrCreatePrefetchCacheEntry @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:227
navigateReducer @ C:\Users\src\client\components\router-reducer\reducers\navigate-reducer.ts:216
clientReducer @ C:\Users\steph\src\client\components\router-reducer\router-reducer.ts:32
action @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:221
runAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:108
dispatchAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:173
dispatch @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:219
eval @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:45
startTransition @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:7967
dispatch @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:44
dispatchAppRouterAction @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:22
dispatchNavigateAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:290
eval @ C:\Users\steph\dev\src\client\app-dir\link.tsx:292
exports.startTransition @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react.development.js:1148
linkClicked @ C:\Users\steph\dev\src\client\app-dir\link.tsx:291
onClick @ C:\Users\steph\dev\src\client\app-dir\link.tsx:639
executeDispatch @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16970
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
processDispatchQueue @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17020
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17621
batchedUpdates$1 @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:3311
dispatchEventForPluginEventSystem @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17174
dispatchEvent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:21357
dispatchDiscreteEvent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:21325
<a>
exports.jsx @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-runtime.development.js:323
LinkComponent @ C:\Users\steph\dev\src\client\app-dir\link.tsx:726
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10857
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15546
renderRootSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15526
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14990
performSyncWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16830
flushSyncWorkAcrossRoots_impl @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16676
processRootScheduleInMicrotask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16714
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16849
<LinkComponent>
exports.jsxDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-dev-runtime.development.js:323
Header @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\components\layout\Header.tsx:189
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10857
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15546
renderRootSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15526
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14990
performSyncWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16830
flushSyncWorkAcrossRoots_impl @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16676
processRootScheduleInMicrotask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16714
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16849
C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:39  Dashboard data fetch error: Error: Given token not valid for any token type
    at apiCall (C:\Users\steph\dev\python_app\mvp_project\frontend\src\lib\proposalAPI.ts:45:11)
    at async fetchDashboardData (C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:29:33)
error @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\next-devtools\userspace\app\errors\intercept-console-error.js:62
fetchDashboardData @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:39
await in fetchDashboardData
ProposerDashboard.useEffect @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:50
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23668
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
commitHookEffectListMount @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:12344
commitHookPassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:12465
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14562
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14609
recursivelyTraverseReconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14533
reconnectPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14555
doubleInvokeEffectsOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16565
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16529
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16535
commitDoubleInvokeEffectsInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16574
flushPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16347
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15973
performWorkUntilDeadline @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\scheduler\cjs\scheduler.development.js:45
<ProposerDashboard>
exports.jsx @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-runtime.development.js:323
ClientPageRoot @ C:\Users\steph\dev\src\client\components\client-page.tsx:60
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10806
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopConcurrentByScheduler @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15720
renderRootConcurrent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15695
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14989
performWorkOnRootViaSchedulerTask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16815
performWorkUntilDeadline @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\scheduler\cjs\scheduler.development.js:45
"use client"
Function.all @ VM496 <anonymous>:1
Function.all @ VM496 <anonymous>:1
initializeElement @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1343
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3066
initializeModelChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1246
resolveModelChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1101
processFullStringRow @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2899
processFullBinaryRow @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2766
processBinaryChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2969
progress @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3233
"use server"
ResponseInstance @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2041
createResponseFromOptions @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3094
exports.createFromReadableStream @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3478
createFromNextReadableStream @ C:\Users\steph\src\client\components\router-reducer\fetch-server-response.ts:388
fetchServerResponse @ C:\Users\steph\src\client\components\router-reducer\fetch-server-response.ts:216
await in fetchServerResponse
eval @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:323
task @ C:\Users\steph\dev\src\client\components\promise-queue.ts:33
processNext @ C:\Users\steph\dev\src\client\components\promise-queue.ts:66
enqueue @ C:\Users\steph\dev\src\client\components\promise-queue.ts:46
createLazyPrefetchEntry @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:322
getOrCreatePrefetchCacheEntry @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:227
navigateReducer @ C:\Users\src\client\components\router-reducer\reducers\navigate-reducer.ts:216
clientReducer @ C:\Users\steph\src\client\components\router-reducer\router-reducer.ts:32
action @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:221
runAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:108
dispatchAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:173
dispatch @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:219
eval @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:45
startTransition @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:7967
dispatch @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:44
dispatchAppRouterAction @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:22
dispatchNavigateAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:290
eval @ C:\Users\steph\dev\src\client\app-dir\link.tsx:292
exports.startTransition @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react.development.js:1148
linkClicked @ C:\Users\steph\dev\src\client\app-dir\link.tsx:291
onClick @ C:\Users\steph\dev\src\client\app-dir\link.tsx:639
executeDispatch @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16970
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
processDispatchQueue @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17020
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17621
batchedUpdates$1 @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:3311
dispatchEventForPluginEventSystem @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17174
dispatchEvent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:21357
dispatchDiscreteEvent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:21325
<a>
exports.jsx @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-runtime.development.js:323
LinkComponent @ C:\Users\steph\dev\src\client\app-dir\link.tsx:726
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10857
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15546
renderRootSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15526
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14990
performSyncWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16830
flushSyncWorkAcrossRoots_impl @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16676
processRootScheduleInMicrotask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16714
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16849
<LinkComponent>
exports.jsxDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-dev-runtime.development.js:323
Header @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\components\layout\Header.tsx:189
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10857
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15546
renderRootSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15526
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14990
performSyncWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16830
flushSyncWorkAcrossRoots_impl @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16676
processRootScheduleInMicrotask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16714
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16849
C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:39  Dashboard data fetch error: Error: Given token not valid for any token type
    at apiCall (C:\Users\steph\dev\python_app\mvp_project\frontend\src\lib\proposalAPI.ts:45:11)
    at async fetchDashboardData (C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:29:33)
error @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\next-devtools\userspace\app\errors\intercept-console-error.js:62
fetchDashboardData @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:39
await in fetchDashboardData
ProposerDashboard.useEffect @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\app\dashboard\proposer\page.tsx:50
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23668
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
commitHookEffectListMount @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:12344
commitHookPassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:12465
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14386
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14389
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14379
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14513
recursivelyTraversePassiveMountEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14359
commitPassiveMountOnFiber @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14398
flushPassiveEffects @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16337
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15973
performWorkUntilDeadline @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\scheduler\cjs\scheduler.development.js:45
<ProposerDashboard>
exports.jsx @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-runtime.development.js:323
ClientPageRoot @ C:\Users\steph\dev\src\client\components\client-page.tsx:60
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10806
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopConcurrentByScheduler @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15720
renderRootConcurrent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15695
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14989
performWorkOnRootViaSchedulerTask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16815
performWorkUntilDeadline @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\scheduler\cjs\scheduler.development.js:45
"use client"
Function.all @ VM496 <anonymous>:1
Function.all @ VM496 <anonymous>:1
initializeElement @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1343
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3066
initializeModelChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1246
resolveModelChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:1101
processFullStringRow @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2899
processFullBinaryRow @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2766
processBinaryChunk @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2969
progress @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3233
"use server"
ResponseInstance @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:2041
createResponseFromOptions @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3094
exports.createFromReadableStream @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-server-dom-webpack\cjs\react-server-dom-webpack-client.browser.development.js:3478
createFromNextReadableStream @ C:\Users\steph\src\client\components\router-reducer\fetch-server-response.ts:388
fetchServerResponse @ C:\Users\steph\src\client\components\router-reducer\fetch-server-response.ts:216
await in fetchServerResponse
eval @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:323
task @ C:\Users\steph\dev\src\client\components\promise-queue.ts:33
processNext @ C:\Users\steph\dev\src\client\components\promise-queue.ts:66
enqueue @ C:\Users\steph\dev\src\client\components\promise-queue.ts:46
createLazyPrefetchEntry @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:322
getOrCreatePrefetchCacheEntry @ C:\Users\steph\src\client\components\router-reducer\prefetch-cache-utils.ts:227
navigateReducer @ C:\Users\src\client\components\router-reducer\reducers\navigate-reducer.ts:216
clientReducer @ C:\Users\steph\src\client\components\router-reducer\router-reducer.ts:32
action @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:221
runAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:108
dispatchAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:173
dispatch @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:219
eval @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:45
startTransition @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:7967
dispatch @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:44
dispatchAppRouterAction @ C:\Users\steph\dev\src\client\components\use-action-queue.ts:22
dispatchNavigateAction @ C:\Users\steph\dev\src\client\components\app-router-instance.ts:290
eval @ C:\Users\steph\dev\src\client\app-dir\link.tsx:292
exports.startTransition @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react.development.js:1148
linkClicked @ C:\Users\steph\dev\src\client\app-dir\link.tsx:291
onClick @ C:\Users\steph\dev\src\client\app-dir\link.tsx:639
executeDispatch @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16970
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
processDispatchQueue @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17020
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17621
batchedUpdates$1 @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:3311
dispatchEventForPluginEventSystem @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:17174
dispatchEvent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:21357
dispatchDiscreteEvent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:21325
<a>
exports.jsx @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-runtime.development.js:323
LinkComponent @ C:\Users\steph\dev\src\client\app-dir\link.tsx:726
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10857
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15546
renderRootSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15526
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14990
performSyncWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16830
flushSyncWorkAcrossRoots_impl @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16676
processRootScheduleInMicrotask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16714
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16849
<LinkComponent>
exports.jsxDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react\cjs\react-jsx-dev-runtime.development.js:323
Header @ C:\Users\steph\dev\python_app\mvp_project\frontend\src\components\layout\Header.tsx:189
react_stack_bottom_frame @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:23583
renderWithHooksAgain @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6892
renderWithHooks @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:6804
updateFunctionComponent @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:9246
beginWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:10857
runWithFiberInDEV @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:871
performUnitOfWork @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15726
workLoopSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15546
renderRootSync @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:15526
performWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:14990
performSyncWorkOnRoot @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16830
flushSyncWorkAcrossRoots_impl @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16676
processRootScheduleInMicrotask @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16714
eval @ C:\Users\steph\dev\python_app\mvp_project\frontend\node_modules\next\dist\compiled\react-dom\cjs\react-dom-client.development.js:16849
```python
# notifications/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('selection', '選出通知'),
        ('adoption', '採用通知'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="通知タイプ")
    title = models.CharField(max_length=100, verbose_name="通知タイトル")
    message = models.TextField(verbose_name="通知メッセージ")
    challenge = models.ForeignKey('challenges.Challenge', on_delete=models.CASCADE, related_name='notifications')
    proposal = models.ForeignKey('proposals.Proposal', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False, verbose_name="既読フラグ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

### 8. 分析・まとめ

```python
# analytics/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Analysis(models.Model):
    challenge = models.OneToOneField('challenges.Challenge', on_delete=models.CASCADE, related_name='analysis')
    most_discussed_proposal = models.ForeignKey('proposals.Proposal', on_delete=models.CASCADE, null=True, blank=True, related_name='most_discussed_analyses')
    most_unique_proposal = models.ForeignKey('proposals.Proposal', on_delete=models.CASCADE, null=True, blank=True, related_name='most_unique_analyses')
    distribution_data = models.JSONField(null=True, blank=True, verbose_name="分布データ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## API ビュー

### 1. 認証関連

```python
# accounts/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, ContributorProfile, ProposerProfile
from .serializers import UserSerializer, ContributorProfileSerializer, ProposerProfileSerializer

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # プロフィール作成
        if user.user_type == 'contributor':
            ContributorProfile.objects.create(user=user, **request.data.get('profile', {}))
        elif user.user_type == 'proposer':
            ProposerProfile.objects.create(user=user, **request.data.get('profile', {}))
        
        # JWTトークン生成
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(username=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
```

### 2. 課題管理

```python
# challenges/views.py
from rest_framework import generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Challenge
from .serializers import ChallengeSerializer

class ChallengeListCreateView(generics.ListCreateAPIView):
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'contributor':
            return Challenge.objects.filter(contributor=user)
        elif user.user_type == 'proposer':
            # 選出された課題のみ表示
            return Challenge.objects.filter(
                selections__proposer=user,
                status='open'
            )
        return Challenge.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(contributor=self.request.user)

class ChallengeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'contributor':
            return Challenge.objects.filter(contributor=user)
        elif user.user_type == 'proposer':
            return Challenge.objects.filter(
                selections__proposer=user
            )
        return Challenge.objects.none()
```

### 3. 提案管理

```python
# proposals/views.py
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Proposal, ProposalComment, ProposalEvaluation
from .serializers import ProposalSerializer, ProposalCommentSerializer, ProposalEvaluationSerializer

class ProposalListCreateView(generics.ListCreateAPIView):
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        challenge_id = self.kwargs.get('challenge_id')
        user = self.request.user
        
        if user.user_type == 'proposer':
            # 選出された提案者のみが提案可能
            return Proposal.objects.filter(
                challenge_id=challenge_id,
                proposer=user
            )
        elif user.user_type == 'contributor':
            # 投稿者は自分の課題の提案を閲覧
            return Proposal.objects.filter(
                challenge_id=challenge_id,
                challenge__contributor=user
            )
        return Proposal.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(proposer=self.request.user)

class ProposalEvaluationView(generics.CreateAPIView):
    serializer_class = ProposalEvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        proposal_id = kwargs.get('proposal_id')
        proposal = Proposal.objects.get(id=proposal_id)
        
        # 同じく選出された提案者のみが評価可能
        if not proposal.challenge.selections.filter(proposer=request.user).exists():
            return Response({'error': 'Not authorized to evaluate'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(proposal=proposal, evaluator=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

## フロントエンド コンポーネント

### 1. 提案カード

```tsx
// components/proposals/ProposalCard.tsx
import React, { useState } from 'react';
import { Proposal } from '@/types/proposal';

interface ProposalCardProps {
  proposal: Proposal;
  userType: 'contributor' | 'proposer';
  onEvaluate?: (proposalId: string, evaluation: 'yes' | 'maybe' | 'no') => void;
  onComment?: (proposalId: string) => void;
  onReport?: (proposalId: string) => void;
}

export function ProposalCard({ 
  proposal, 
  userType, 
  onEvaluate, 
  onComment, 
  onReport 
}: ProposalCardProps) {
  const [showComments, setShowComments] = useState(false);
  const [evaluation, setEvaluation] = useState<'yes' | 'maybe' | 'no' | null>(null);

  const handleEvaluation = (evalType: 'yes' | 'maybe' | 'no') => {
    setEvaluation(evalType);
    onEvaluate?.(proposal.id, evalType);
  };

  const getEvaluationScore = () => {
    const scores = proposal.evaluations.reduce((acc, eval) => {
      if (eval.evaluation === 'no') acc += 2;
      else if (eval.evaluation === 'maybe') acc += 1;
      return acc;
    }, 0);
    return scores;
  };

  return (
    <div className={`border rounded-lg p-4 mb-4 ${
      evaluation ? 'bg-gray-100 opacity-75' : 'bg-white'
    }`}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold">{proposal.proposer.full_name}</h3>
        <span className="text-sm text-gray-500">
          {new Date(proposal.created_at).toLocaleDateString()}
        </span>
      </div>
      
      <div className="mb-4">
        <h4 className="font-medium mb-2">【結論】</h4>
        <p className="text-gray-700">{proposal.conclusion}</p>
      </div>
      
      <div className="mb-4">
        <h4 className="font-medium mb-2">【理由】</h4>
        <p className="text-gray-700">{proposal.reasoning}</p>
      </div>
      
      {userType === 'proposer' && !evaluation && (
        <div className="mb-4">
          <p className="text-sm font-medium mb-2">この回答を事前に思い付いたか？</p>
          <div className="flex gap-2">
            <button
              onClick={() => handleEvaluation('yes')}
              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Yes
            </button>
            <button
              onClick={() => handleEvaluation('maybe')}
              className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600"
            >
              Maybe
            </button>
            <button
              onClick={() => handleEvaluation('no')}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              No
            </button>
          </div>
        </div>
      )}
      
      <div className="flex justify-between items-center">
        <div className="flex gap-4">
          <button
            onClick={() => setShowComments(!showComments)}
            className="text-blue-500 hover:text-blue-700"
          >
            コメントを見る ({proposal.comments.length})
          </button>
          <button
            onClick={() => onReport?.(proposal.id)}
            className="text-red-500 hover:text-red-700"
          >
            報告
          </button>
        </div>
        
        <div className="text-sm text-gray-500">
          独自性スコア: {getEvaluationScore()}
        </div>
      </div>
      
      {showComments && (
        <div className="mt-4 border-t pt-4">
          <ProposalCommentList 
            proposalId={proposal.id}
            comments={proposal.comments}
          />
        </div>
      )}
    </div>
  );
}
```

### 2. コメント機能

```tsx
// components/proposals/ProposalCommentList.tsx
import React, { useState } from 'react';
import { ProposalComment } from '@/types/proposal';

interface ProposalCommentListProps {
  proposalId: string;
  comments: ProposalComment[];
  onAddComment?: (comment: Omit<ProposalComment, 'id' | 'created_at'>) => void;
  onReply?: (commentId: string, reply: string) => void;
  onReference?: (commentId: string) => void;
  onReport?: (commentId: string) => void;
}

export function ProposalCommentList({ 
  proposalId, 
  comments, 
  onAddComment, 
  onReply, 
  onReference, 
  onReport 
}: ProposalCommentListProps) {
  const [showCommentForm, setShowCommentForm] = useState(false);
  const [newComment, setNewComment] = useState({
    target_section: 'reasoning' as 'reasoning' | 'inference',
    conclusion: '',
    reasoning: ''
  });

  const handleSubmitComment = () => {
    onAddComment?.(newComment);
    setNewComment({ target_section: 'reasoning', conclusion: '', reasoning: '' });
    setShowCommentForm(false);
  };

  return (
    <div>
      <h4 className="font-medium mb-3">コメント一覧</h4>
      
      {comments.map((comment) => (
        <div key={comment.id} className="border rounded p-3 mb-3">
          <div className="flex justify-between items-start mb-2">
            <span className="font-medium">{comment.commenter.full_name}</span>
            <span className="text-sm text-gray-500">
              {new Date(comment.created_at).toLocaleDateString()}
            </span>
          </div>
          
          <div className="mb-2">
            <span className="text-sm bg-blue-100 px-2 py-1 rounded">
              {comment.target_section === 'reasoning' ? '理由' : '推論過程'}へのコメント
            </span>
          </div>
          
          <div className="mb-2">
            <h5 className="font-medium">【結論】</h5>
            <p className="text-gray-700">{comment.conclusion}</p>
          </div>
          
          <div className="mb-3">
            <h5 className="font-medium">【理由】</h5>
            <p className="text-gray-700">{comment.reasoning}</p>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => onReply?.(comment.id, '')}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              返信
            </button>
            <button
              onClick={() => onReference?.(comment.id)}
              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
            >
              参考
            </button>
            <button
              onClick={() => onReport?.(comment.id)}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              報告
            </button>
          </div>
        </div>
      ))}
      
      {!showCommentForm ? (
        <button
          onClick={() => setShowCommentForm(true)}
          className="w-full py-2 border-2 border-dashed border-gray-300 rounded hover:border-gray-400"
        >
          コメントを追加
        </button>
      ) : (
        <div className="border rounded p-4">
          <h5 className="font-medium mb-3">コメント投稿</h5>
          
          <div className="mb-3">
            <label className="block text-sm font-medium mb-1">コメント対象</label>
            <select
              value={newComment.target_section}
              onChange={(e) => setNewComment({
                ...newComment,
                target_section: e.target.value as 'reasoning' | 'inference'
              })}
              className="w-full p-2 border rounded"
            >
              <option value="reasoning">理由</option>
              <option value="inference">推論過程</option>
            </select>
          </div>
          
          <div className="mb-3">
            <label className="block text-sm font-medium mb-1">結論</label>
            <textarea
              value={newComment.conclusion}
              onChange={(e) => setNewComment({ ...newComment, conclusion: e.target.value })}
              className="w-full p-2 border rounded"
              rows={3}
            />
          </div>
          
          <div className="mb-3">
            <label className="block text-sm font-medium mb-1">理由</label>
            <textarea
              value={newComment.reasoning}
              onChange={(e) => setNewComment({ ...newComment, reasoning: e.target.value })}
              className="w-full p-2 border rounded"
              rows={3}
            />
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={handleSubmitComment}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              投稿
            </button>
            <button
              onClick={() => setShowCommentForm(false)}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              キャンセル
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 3. 分析・まとめ

```tsx
// components/analytics/SummaryCard.tsx
import React, { useState } from 'react';
import { Analysis } from '@/types/analytics';

interface SummaryCardProps {
  analysis: Analysis;
  onViewMore?: (type: 'discussion' | 'uniqueness') => void;
}

export function SummaryCard({ analysis, onViewMore }: SummaryCardProps) {
  const [showDistribution, setShowDistribution] = useState(false);

  return (
    <div className="bg-white border rounded-lg p-6">
      <h2 className="text-xl font-bold mb-6">回答まとめ</h2>
      
      {/* 最も議論になった回答 */}
      {analysis.most_discussed_proposal && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">【最も議論になった回答】</h3>
          <div className="border rounded p-4">
            <div className="flex justify-between items-start mb-2">
              <span className="font-medium">
                {analysis.most_discussed_proposal.proposer.full_name}
              </span>
              <span className="text-sm text-gray-500">
                コメント数: {analysis.most_discussed_proposal.comments.length}件
              </span>
            </div>
            <div className="mb-2">
              <h4 className="font-medium">【結論】</h4>
              <p className="text-gray-700">{analysis.most_discussed_proposal.conclusion}</p>
            </div>
            <div className="mb-3">
              <h4 className="font-medium">【理由】</h4>
              <p className="text-gray-700">{analysis.most_discussed_proposal.reasoning}</p>
            </div>
            <button
              onClick={() => onViewMore?.('discussion')}
              className="text-blue-500 hover:text-blue-700"
            >
              もっと見る
            </button>
          </div>
        </div>
      )}
      
      {/* 最も独自性の高い回答 */}
      {analysis.most_unique_proposal && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">【最も独自性の高い回答】</h3>
          <div className="border rounded p-4">
            <div className="flex justify-between items-start mb-2">
              <span className="font-medium">
                {analysis.most_unique_proposal.proposer.full_name}
              </span>
              <span className="text-sm text-gray-500">
                独自性スコア: {analysis.most_unique_proposal.evaluations.reduce((acc, eval) => {
                  if (eval.evaluation === 'no') acc += 2;
                  else if (eval.evaluation === 'maybe') acc += 1;
                  return acc;
                }, 0)}点
              </span>
            </div>
            <div className="mb-2">
              <h4 className="font-medium">【結論】</h4>
              <p className="text-gray-700">{analysis.most_unique_proposal.conclusion}</p>
            </div>
            <div className="mb-3">
              <h4 className="font-medium">【理由】</h4>
              <p className="text-gray-700">{analysis.most_unique_proposal.reasoning}</p>
            </div>
            <button
              onClick={() => onViewMore?.('uniqueness')}
              className="text-blue-500 hover:text-blue-700"
            >
              もっと見る
            </button>
          </div>
        </div>
      )}
      
      {/* 回答の分布 */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">【回答の分布】</h3>
        <button
          onClick={() => setShowDistribution(!showDistribution)}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          {showDistribution ? '分布を隠す' : '分布を表示'}
        </button>
        {showDistribution && (
          <div className="mt-4 p-4 border rounded">
            <div className="text-center text-gray-500">
              分布図の実装（チャートライブラリ使用）
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

## TypeScript型定義

```typescript
// types/proposal.ts
export interface Proposal {
  id: string;
  challenge: {
    id: string;
    title: string;
  };
  proposer: {
    id: string;
    full_name: string;
  };
  conclusion: string;
  reasoning: string;
  is_adopted: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  comments: ProposalComment[];
  evaluations: ProposalEvaluation[];
}

export interface ProposalComment {
  id: string;
  proposal: string;
  commenter: {
    id: string;
    full_name: string;
  };
  target_section: 'reasoning' | 'inference';
  conclusion: string;
  reasoning: string;
  is_deleted: boolean;
  created_at: string;
}

export interface ProposalEvaluation {
  id: string;
  proposal: string;
  evaluator: {
    id: string;
    full_name: string;
  };
  evaluation: 'yes' | 'maybe' | 'no';
  created_at: string;
}

// types/analytics.ts
export interface Analysis {
  id: string;
  challenge: string;
  most_discussed_proposal?: Proposal;
  most_unique_proposal?: Proposal;
  distribution_data?: any;
  created_at: string;
  updated_at: string;
}
```

## サービス・ロジック

### 1. 選出機能

```python
# selection/services.py
import random
from django.db import transaction
from .models import Selection
from challenges.models import Challenge
from notifications.models import Notification

class SelectionService:
    @staticmethod
    def select_proposers(challenge_id: int):
        challenge = Challenge.objects.get(id=challenge_id)
        required_count = challenge.required_participants
        
        # 提案者候補を取得（利用停止中でないユーザー）
        available_proposers = User.objects.filter(
            user_type='proposer',
            suspensions__is_active=False
        ).exclude(
            id__in=Selection.objects.filter(challenge=challenge).values_list('proposer_id', flat=True)
        )
        
        # ランダム選出
        selected_proposers = random.sample(
            list(available_proposers), 
            min(required_count, len(available_proposers))
        )
        
        # 選出記録を作成
        with transaction.atomic():
            for proposer in selected_proposers:
                Selection.objects.create(
                    challenge=challenge,
                    proposer=proposer
                )
                
                # 通知を作成
                Notification.objects.create(
                    user=proposer,
                    notification_type='selection',
                    title='課題に選出されました',
                    message=f'{challenge.title}の課題に選出されました',
                    challenge=challenge
                )
        
        return selected_proposers
```

### 2. 分析・まとめ機能

```python
# analytics/services.py
from django.db.models import Count, Q
from .models import Analysis
from proposals.models import Proposal, ProposalEvaluation

class AnalyticsService:
    @staticmethod
    def generate_analysis(challenge_id: int):
        challenge = Challenge.objects.get(id=challenge_id)
        proposals = Proposal.objects.filter(challenge=challenge, is_deleted=False)
        
        # 最も議論になった回答（コメント数最多）
        most_discussed = proposals.annotate(
            comment_count=Count('comments', filter=Q(comments__is_deleted=False))
        ).order_by('-comment_count').first()
        
        # 最も独自性の高い回答（評価スコア最高）
        most_unique = None
        max_score = 0
        
        for proposal in proposals:
            score = 0
            for evaluation in proposal.evaluations.all():
                if evaluation.evaluation == 'no':
                    score += 2
                elif evaluation.evaluation == 'maybe':
                    score += 1
            
            if score > max_score:
                max_score = score
                most_unique = proposal
        
        # 分析結果を作成
        analysis, created = Analysis.objects.get_or_create(
            challenge=challenge,
            defaults={
                'most_discussed_proposal': most_discussed,
                'most_unique_proposal': most_unique,
                'distribution_data': AnalyticsService._generate_distribution_data(proposals)
            }
        )
        
        if not created:
            analysis.most_discussed_proposal = most_discussed
            analysis.most_unique_proposal = most_unique
            analysis.distribution_data = AnalyticsService._generate_distribution_data(proposals)
            analysis.save()
        
        return analysis
    
    @staticmethod
    def _generate_distribution_data(proposals):
        # 回答の類似度分析やクラスタリングの実装
        # ここでは簡易的な実装例
        return {
            'total_proposals': proposals.count(),
            'categories': [
                {'name': 'カテゴリA', 'count': 5},
                {'name': 'カテゴリB', 'count': 3},
                {'name': 'カテゴリC', 'count': 2},
            ]
        }
```

この実装例により、PROJECT_DESIGN.mdで定義した機能を具体的なコードで実現できます。特に、ご指摘いただいた重要な機能（評価システム、コメント機能、分析・まとめ機能等）を詳細に実装しています。
