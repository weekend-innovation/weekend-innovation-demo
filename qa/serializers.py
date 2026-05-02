from rest_framework import serializers

from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    asked_by_username = serializers.ReadOnlyField(source="asked_by.username")
    answered_by_username = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "asked_by",
            "asked_by_username",
            "question_text",
            "answer_text",
            "answered_by",
            "answered_by_username",
            "answered_at",
            "status",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "asked_by",
            "asked_by_username",
            "answered_by",
            "answered_by_username",
            "answered_at",
            "created_at",
            "updated_at",
        ]

    def get_answered_by_username(self, obj):
        if obj.answer_text and obj.answer_text.strip():
            return "Weekend Innovation 運営"
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if not request or not getattr(request.user, "is_authenticated", False):
            return data
        # 運営（staff）は管理用に全項目をそのまま返す
        if request.user.is_staff:
            return data
        # 公開済みQ&A は質問者名・日時を返さない（遠慮・対応時間の評価を避ける）
        if instance.status == Question.STATUS_ANSWERED and instance.is_public:
            data["asked_by_username"] = ""
            data["created_at"] = None
            data["answered_at"] = None
            if instance.asked_by_id != request.user.id:
                data["asked_by"] = None
        return data


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["question_text"]

    def validate_question_text(self, value):
        text = (value or "").strip()
        if len(text) < 5:
            raise serializers.ValidationError("質問は5文字以上で入力してください。")
        if len(text) > 2000:
            raise serializers.ValidationError("質問は2000文字以内で入力してください。")
        return text


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["answer_text", "status", "is_public"]

    def validate_answer_text(self, value):
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError("回答内容は必須です。")
        return text

