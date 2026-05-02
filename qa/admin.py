from django.contrib import admin

from .models import Question


OPERATOR_LABEL = "Weekend Innovation 運営"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "asked_by",
        "short_question",
        "status",
        "is_public",
        "operator_display",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "is_public", "created_at")
    search_fields = ("asked_by__username", "question_text", "answer_text")
    readonly_fields = ("created_at", "updated_at", "answered_at", "operator_display")

    fieldsets = (
        ("質問", {"fields": ("asked_by", "question_text", "created_at", "updated_at")}),
        ("回答", {"fields": ("answer_text", "operator_display", "answered_at")}),
        ("公開設定", {"fields": ("status", "is_public")}),
    )

    def short_question(self, obj):
        return obj.question_text[:30]

    short_question.short_description = "質問内容"

    def operator_display(self, obj):
        if obj.answer_text and obj.answer_text.strip():
            return OPERATOR_LABEL
        return "-"

    operator_display.short_description = "回答者"
