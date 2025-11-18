from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, View
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django_htmx.http import HttpResponseClientRefresh
from .models import Lesson
from .forms import LessonForm
from .tasks import create_lesson_task
from celery.result import AsyncResult


class LessonListView(ListView):
    model = Lesson
    template_name = "lessons/lesson_list.html"
    context_object_name = "lessons"
    ordering = ["-scheduled_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        view = LessonCreateView()
        view.request = self.request
        context["form"] = view.get_form()
        context["task_id"] = self.request.session.get("task_id")
        return context


class LessonCreateView(CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = "lessons/lesson_form.html"
    success_url = reverse_lazy("lesson_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        task = create_lesson_task.delay(self.object.id)
        self.request.session["task_id"] = task.id
        return response


class LessonCompleteView(UpdateView):
    model = Lesson
    fields = []
    success_url = reverse_lazy("lesson_list")

    def post(self, request, *args, **kwargs):
        lesson = self.get_object()
        lesson.status = "completed"
        lesson.save()
        return HttpResponseClientRefresh()


class TaskStatusView(View):
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        if result.state == "PENDING":
            status = "Урок Создан"
            is_complete = False
        elif result.state == "PROGRESS":
            status = result.info.get("status", "Отправляем уведомления ученикам")
            is_complete = False
        elif result.state == "SUCCESS":
            status = "Уведомления отправлены"
            is_complete = True
            # Очищаем task_id из сессии когда задача завершена
            if "task_id" in request.session:
                del request.session["task_id"]
        else:
            status = "Ошибка"
            is_complete = True
            # Очищаем task_id из сессии при ошибке
            if "task_id" in request.session:
                del request.session["task_id"]
        return render(
            request,
            "lessons/partials/task_status.html",
            {"status": status, "is_complete": is_complete},
        )
