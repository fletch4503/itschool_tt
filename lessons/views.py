import time
from itschooltt.utils import log
from django.shortcuts import render
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    # View,
)
from django.urls import reverse_lazy
from django.views.decorators.http import (
    require_http_methods,
    # require_POST,
    # require_GET,
)
from django_htmx.http import HttpResponseClientRefresh
from django_htmx.middleware import HtmxDetails
from .models import Lesson
from .forms import LessonForm
from .tasks import create_lesson_task
from celery.result import AsyncResult
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from itschooltt.celery import current_app as app

# from django.contrib import messages


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
    model = Lesson
    template_name = "lessons/lesson_list.html"
    context_object_name = "lessons"
    ordering = ["-id"]

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

    # def dispatch(self, request, *args, **kwargs):
    #     log.info(
    #         f"LessonCreateView dispatch: method={request.method}, htmx={getattr(request, 'htmx', None)}"
    #     )
    #     return super().dispatch(request, *args, **kwargs)
    #
    def form_valid(self, form):
        log.info("Form is valid, creating lesson")
        response = super().form_valid(form)
        lessn_id = self.object.id
        try:
            task = create_lesson_task.delay(lessn_id)
            time.sleep(2)
            self.request.session["task_id"] = task.id
        except Exception as e:
            log.error(f"Не получили результата из Celery c ошибкой: {e}")
        # if self.request.htmx:
        task_id = self.request.session.get("task_id")
        lessn = self.object
        res = AsyncResult(task.id, app=app)
        context = self.get_context_data(form=form)
        context = {
            "task_id": task_id,
            "lesson": lessn,
            "status": res.state,
            "HX-Trigger": "create_run",
        }
        log.warning("Передаем в форму контекст %s", context)
        response = render(
            self.request,
            "lessons/partials/task_status.html#task-status-info",
            context,
        )
        response["HX-Trigger"] = "create_run"
        self.request.session["task_id"] = task.id
        if res.state in ["PENDING", "PROGRESS"]:
            return HttpResponseRedirect(
                reverse_lazy("task_status", kwargs={"task_id": task_id})
            )
        else:
            return response


# class TaskStatusView(View):
#     def get(self, request, task_id):
@counter
@require_http_methods(["GET"])
def task_status(request: HtmxHttpRequest, task_id) -> HttpResponse:
    global count_status
    count_status += 1
    task_id = request.GET.get("task_id") or task_id
    template_name = "lessons/partials/task_status.html"
    if request.htmx:
        log.warning("Итерация %s", count_status)
        template_name += "#task-status-info"
    res = AsyncResult(task_id, app=app)
    log.warning("Текущий статус %s", res.state)
    context = {
        "task_id": task_id,
        "task_result": count_status,
        "status": res.state,
    }
    response = render(request, template_name=template_name, context=context)
    log.warning("Отправляем в форму контекст %s", context)
    if res.state == "SUCCESS":
        count_status = 0
        context["status"] = "SUCCESS"
        response = render(request, template_name=template_name, context=context)
        response["HX-Trigger"] = "success"
        # Очищаем task_id из сессии когда задача завершена
        if "task_id" in request.session:
            del request.session["task_id"]
        log.warning("Отправляем в форму контекст %s", context)
        return HttpResponseClientRefresh()
    elif res.state == "FAILURE":
        count_status = 0
        context["status"] = "FAILURE"
        response = render(request, template_name=template_name, context=context)
        response["HX-Trigger"] = "failure"
        log.warning("Отправляем в форму контекст %s", context)
        return HttpResponseClientRefresh()
    else:
        response = render(request, template_name=template_name, context=context)
        log.warning("Отправляем в форму контекст %s", context)
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
