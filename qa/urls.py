from django.urls import path

from .views import QuestionListCreateView, QuestionAnswerView


app_name = "qa"

urlpatterns = [
    path("questions/", QuestionListCreateView.as_view(), name="question-list-create"),
    path("questions/<int:pk>/answer/", QuestionAnswerView.as_view(), name="question-answer"),
]

