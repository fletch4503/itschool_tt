import time
from itschooltt.utils import log
from django.shortcuts import render
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    View,
)
from django.urls import reverse_lazy
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_GET,
)
from django_htmx.http import HttpResponseClientRefresh
from django_htmx.middleware import HtmxDetails
from .models import Lesson
from .forms import LessonForm
from .tasks import create_lesson_task
from celery.result import AsyncResult
from django.http import HttpResponse, HttpRequest
from itschooltt.celery import current_app as app

# from django.contrib import messages


count_status = 0


def counter(func):
    global count_status
    count_status = 0

    def wrapper(*args, **kwargs):
        wrapper.count_status += 1  # Увеличиваем счётчик при каждом вызове функции
        logger.info(
            f"Функция {func.__name__} была вызвана {wrapper.count_status} раз(а)"
        )
        return func(*args, **kwargs)

    wrapper.count_status = 0  # Инициализируем счётчик
    return wrapper


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


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
        try:
            task = create_lesson_task.delay(self.object.id)
            time.sleep(2)
            self.request.session["task_id"] = task.id
        except Exception as e:
            log.error(f"Не получили результата из Celery c ошибкой: {e}")
        # return response
        return HttpResponseClientRefresh()


# class TaskStatusView(View):
#     def get(self, request, task_id):
@counter
@require_http_methods(["GET"])
def task_status(request: HtmxHttpRequest, task_id) -> HttpResponse:
    global count_status
    count_status += 1
    task_id = request.GET.get("task_id") or task_id
    template_name = "lessons/task_status.html"
    if request.htmx:
        log.warning("Итерация %s", count_status)
        template_name += "#task-status-info"
    res = AsyncResult(task_id, app=app)
    log.warning("Текущий статус %s", res.state)
    if res.state == "PENDING":
        status = "Урок Создан"
        is_complete = False
    elif res.state == "PROGRESS":
        status = res.info.get("status", "Отправляем уведомления ученикам")
        is_complete = False
    elif res.state == "SUCCESS":
        status = "Уведомления отправлены"
        is_complete = True
        response["HX-Trigger"] = "success"
        # Очищаем task_id из сессии когда задача завершена
        if "task_id" in request.session:
            del request.session["task_id"]
        return HttpResponseClientRefresh()
    else:
        status = "Ошибка"
        is_complete = True
        response["HX-Trigger"] = "failure"
        # Очищаем task_id из сессии при ошибке
        if "task_id" in request.session:
            del request.session["task_id"]
    context = {
        "task_id": task_id,
        "task_result": count_status,
        "HX-Trigger": "task_run",
        "status": status,
        "is_complete": is_complete,
    }
    response = render(request, template_name=template_name, context=context)
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
