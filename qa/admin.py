from django.contrib import admin

from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "asked_by",
        "short_question",
        "status",
        "is_public",
        "answered_by",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "is_public", "created_at")
    search_fields = ("asked_by__username", "question_text", "answer_text")
    readonly_fields = ("created_at", "updated_at", "answered_at")

    fieldsets = (
        ("質問", {"fields": ("asked_by", "question_text", "created_at", "updated_at")}),
        ("回答", {"fields": ("answer_text", "answered_by", "answered_at")}),
        ("公開設定", {"fields": ("status", "is_public")}),
    )

    def short_question(self, obj):
        return obj.question_text[:30]

    short_question.short_description = "質問内容"

