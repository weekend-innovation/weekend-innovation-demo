from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_text", models.TextField(verbose_name="質問内容")),
                ("answer_text", models.TextField(blank=True, verbose_name="回答内容")),
                ("answered_at", models.DateTimeField(blank=True, null=True, verbose_name="回答日時")),
                ("status", models.CharField(choices=[("pending", "回答待ち"), ("answered", "回答済み"), ("hidden", "非表示")], default="pending", max_length=20, verbose_name="状態")),
                ("is_public", models.BooleanField(default=False, help_text="回答済みで公開対象のQ&Aのみ一般表示されます。", verbose_name="公開する")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="作成日時")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新日時")),
                ("answered_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="qa_answers", to=settings.AUTH_USER_MODEL, verbose_name="回答者")),
                ("asked_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="qa_questions", to=settings.AUTH_USER_MODEL, verbose_name="質問者")),
            ],
            options={
                "verbose_name": "質問",
                "verbose_name_plural": "質問",
                "ordering": ["-created_at"],
            },
        ),
    ]

