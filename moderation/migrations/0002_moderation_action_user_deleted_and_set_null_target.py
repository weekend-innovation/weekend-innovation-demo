# Generated manually for admin moderation: preserve action log after user delete

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("moderation", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="moderationaction",
            name="action_type",
            field=models.CharField(
                choices=[
                    ("report_created", "報告作成"),
                    ("report_reviewed", "報告審査"),
                    ("report_resolved", "報告解決"),
                    ("user_suspended", "ユーザー停止"),
                    ("user_unsuspended", "ユーザー停止解除"),
                    ("user_deleted", "ユーザー削除"),
                    ("content_hidden", "コンテンツ非表示"),
                    ("content_deleted", "コンテンツ削除"),
                ],
                max_length=30,
                verbose_name="アクションタイプ",
            ),
        ),
        migrations.AlterField(
            model_name="moderationaction",
            name="target_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="actions_against",
                to=settings.AUTH_USER_MODEL,
                verbose_name="対象ユーザー",
            ),
        ),
    ]
