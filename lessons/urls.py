from django.urls import path

from . import views

urlpatterns = [
    path("", views.LessonListView.as_view(), name="lesson_list"),
    path("create/", views.LessonCreateView.as_view(), name="lesson_create"),
    path(
        "<int:pk>/complete/", views.LessonCompleteView.as_view(), name="lesson_complete"
    ),
    path(
        "task-status/<str:task_id>/", views.TaskStatusView.as_view(), name="task_status"
    ),
]
