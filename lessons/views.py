from itschooltt.utils import log
from django.shortcuts import render
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
)
from django.urls import reverse_lazy
from django.core.cache import cache
from django.views.decorators.http import (
    require_http_methods,
)
from django_htmx.http import HttpResponseClientRefresh
from django_htmx.middleware import HtmxDetails
from .models import Lesson
from .forms import LessonForm
from .tasks import create_lesson_task
from celery.result import AsyncResult
from django.http import (
    HttpResponse,
    HttpRequest,
)
from itschooltt.celery import current_app
import time

count_status = 0


def counter(func):
    global count_status
    count_status = 0

    def wrapper(*args, **kwargs):
        wrapper.count_status += 1  # Увеличиваем счётчик при каждом вызове функции
        log.info(f"Функция {func.__name__} была вызвана {wrapper.count_status} раз(а)")
        return func(*args, **kwargs)

    wrapper.count_status = 0  # Инициализируем счётчик
    return wrapper


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


class LessonListView(ListView):
    """
    Отображаем список уроков на главной странице
    """

    model = Lesson
    template_name = "lessons/lesson_list.html"
    context_object_name = "lessons"
    ordering = ["-id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        log.info(
            "Передаем в lesson_list.html статус: %s и набор длиной: %s",
            status,
            len(queryset),
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        view = LessonCreateView()
        view.request = self.request
        context["form"] = view.get_form()
        task_id = self.request.session.get("task_id")
        context["task_id"] = task_id
        log.info("Передаем в lesson_list.html task_id: %s", task_id)
        return context


class LessonCreateView(CreateView):
    """
    Создаем новый урок
    """

    model = Lesson
    form_class = LessonForm
    template_name = "lessons/partials/lesson_row.html"
    success_url = reverse_lazy("lessons:lesson_list")

    def form_valid(self, form):
        cache.clear()
        self.request.session.pop("task_id", None)  # Сбрасываем задачу
        response = super().form_valid(form)
        context = self.get_context_data(form=form)
        lesson = self.object
        lesson_id = self.object.id
        log.info(
            "Form is valid, creating lesson: %s and context: %s", lesson_id, context
        )
        try:
            task = create_lesson_task.delay(lesson_id)
        except Exception as e:
            log.error(f"Не получили результата из Celery c ошибкой: {e}")
        res = AsyncResult(task.id, app=current_app)
        context = {
            "task_id": task.id,
            "lesson_id": lesson_id,
            "lesson": lesson,
            "status": "Отправляем уведомления",
            "HX-Trigger": "create_run",
        }
        log.warning("Передаем в форму контекст %s", context)
        response = render(
            self.request,
            self.template_name,
            context,
        )
        response["HX-Trigger"] = "create_run"
        self.request.session["task_id"] = task.id
        self.request.session["status"] = res.state
        self.request.session["lesson_id"] = lesson_id
        self.request.session["task_result"] = 1
        log.info("Выходим из FormValid")
        return HttpResponseClientRefresh()


@counter
@require_http_methods(["GET"])
def task_status(request: HtmxHttpRequest, task_id) -> HttpResponse:
    """
    Отображаем статус отправки уведомлений ученикам после создания урока
    """
    global count_status
    count_status += 1
    task_id = request.GET.get("task_id") or task_id
    lesson_id = request.session.get("lesson_id")
    extstatus = request.session.get("status")
    template_name = "lessons/partials/task_status.html#task-status-info"
    res = AsyncResult(task_id, app=current_app)
    time.sleep(2)
    if request.htmx:
        log.warning(
            "Итерация %s, task_id: %s, Ext_Status: %s, Task Status: %s",
            count_status,
            task_id,
            extstatus,
            res.state,
        )
    context = {
        "task_id": task_id,
        "lesson_id": lesson_id,
        "task_result": count_status,
        # "status": res.state,
        "status": "Отправляем уведомления",
    }
    response = render(request, template_name=template_name, context=context)
    if res.state == "SUCCESS":
        count_status = 0
        context["status"] = "SUCCESS"
        response = render(request, template_name=template_name, context=context)
        response["HX-Trigger"] = "success"
        # Очищаем task_id и lesson_id из сессии когда задача завершена
        request.session.pop("task_id", None)
        request.session.pop("lesson_id", None)
        log.warning("Текущий статус: %s и контекст: %s", res.state, context)
        return HttpResponseClientRefresh()
    elif res.state == "FAILURE":
        count_status = 0
        context["status"] = "FAILURE"
        response = render(request, template_name=template_name, context=context)
        response["HX-Trigger"] = "failure"
        # Очищаем task_id и lesson_id из сессии при ошибке
        request.session.pop("task_id", None)
        request.session.pop("lesson", None)
        log.warning("Текущий статус: %s и контекст: %s", res.state, context)
        return HttpResponseClientRefresh()
    else:
        response = render(request, template_name=template_name, context=context)
        log.warning("Отправляем в форму контекст %s", context)
        return response


class LessonCompleteView(UpdateView):
    """
    Вручную меняем статус урока на 'Завершен'.
    Для полного функционала нужна отдельная задача в Celery-beat, отслеживающая
    даты уроков по отношению к текущей и изменяющая статус, если дата 'просрочена'
    """

    model = Lesson
    fields = []
    success_url = reverse_lazy("lessons:lesson_list")

    def post(self, request, *args, **kwargs):
        lesson = self.get_object()
        lesson.status = "completed"
        lesson.save()
        return HttpResponseClientRefresh()
