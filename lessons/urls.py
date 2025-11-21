from django.urls import path
from . import views

app_name = "lessons"
urlpatterns = [
    path(
        "", views.LessonListView.as_view(), name="lesson_list"
    ),  # Отображаем список уроков
    path(
        "create/", views.LessonCreateView.as_view(), name="lesson_create"
    ),  # Создаем урок
    path(
        "<int:pk>/complete/",
        views.LessonCompleteView.as_view(),
        name="lesson_complete",
        # Меняем статус урока на Завершен
    ),
    path(
        "task-status/<str:task_id>/",  # Отслеживаем статус задачи отправки уведомлений
        views.task_status,
        name="task_status",
    ),
]
