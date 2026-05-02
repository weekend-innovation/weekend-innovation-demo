from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Question
from .serializers import (
    QuestionSerializer,
    QuestionCreateSerializer,
    QuestionAnswerSerializer,
)


class QuestionListCreateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 一般ユーザー: 公開済みQ&A + 自分の質問
        public_qs = Question.objects.filter(
            status=Question.STATUS_ANSWERED,
            is_public=True,
        )
        own_qs = Question.objects.filter(asked_by=request.user)

        if request.user.is_staff:
            queryset = Question.objects.all()
        else:
            queryset = (public_qs | own_qs).distinct().order_by("-created_at")

        serializer = QuestionSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = Question.objects.create(
            asked_by=request.user,
            question_text=serializer.validated_data["question_text"],
            status=Question.STATUS_PENDING,
            is_public=False,
        )
        return Response(
            QuestionSerializer(question, context={"request": request}).data,
            status=201,
        )


class QuestionAnswerView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Question.objects.all()
    serializer_class = QuestionAnswerSerializer

    def perform_update(self, serializer):
        answer_text = serializer.validated_data.get("answer_text", "").strip()
        status_value = serializer.validated_data.get("status", Question.STATUS_ANSWERED)
        is_public = serializer.validated_data.get("is_public", False)

        serializer.save(
            answer_text=answer_text,
            status=status_value,
            is_public=is_public,
            answered_by=self.request.user,
            answered_at=timezone.now(),
        )

