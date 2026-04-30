from django.conf import settings
from django.db import models
from django.utils import timezone


class Question(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ANSWERED = "answered"
    STATUS_HIDDEN = "hidden"
    STATUS_CHOICES = [
        (STATUS_PENDING, "回答待ち"),
        (STATUS_ANSWERED, "回答済み"),
        (STATUS_HIDDEN, "非表示"),
    ]

    asked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="qa_questions",
        verbose_name="質問者",
    )
    question_text = models.TextField(verbose_name="質問内容")
    answer_text = models.TextField(blank=True, verbose_name="回答内容")
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="qa_answers",
        verbose_name="回答者",
    )
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="回答日時")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="状態",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="公開する",
        help_text="回答済みで公開対象のQ&Aのみ一般表示されます。",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "質問"
        verbose_name_plural = "質問"

    def __str__(self):
        return f"{self.asked_by.username}: {self.question_text[:40]}"

    def save(self, *args, **kwargs):
        if self.answer_text.strip():
            if self.status == self.STATUS_PENDING:
                self.status = self.STATUS_ANSWERED
            if self.answered_at is None:
                self.answered_at = timezone.now()
        elif self.status == self.STATUS_ANSWERED:
            self.status = self.STATUS_PENDING
            self.answered_at = None
            self.is_public = False
        super().save(*args, **kwargs)

