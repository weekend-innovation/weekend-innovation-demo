from rest_framework import serializers

from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    asked_by_username = serializers.ReadOnlyField(source="asked_by.username")
    answered_by_username = serializers.ReadOnlyField(source="answered_by.username")

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

