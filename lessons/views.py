from itschooltt.utils import log
from django.shortcuts import render
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    # View,
)
from django.urls import reverse_lazy
from django.core.cache import cache
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
from django.http import (
    HttpResponse,
    HttpRequest,
    HttpResponseRedirect,
)
from itschooltt.celery import current_app
import time

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
        context["task_id"] = self.request.session.get("task_id")
        log.info("Передаем в lesson_list.html task_id: %s", context["task_id"])
        return context


class LessonCreateView(CreateView):
    model = Lesson
    form_class = LessonForm
    # template_name = "lessons/lesson_form.html"
    template_name = "lessons/partials/lesson_row.html"
    # template_name = "lessons/partials/task_status.html#task-status-info"
    success_url = reverse_lazy("lessons:lesson_list")

    def form_valid(self, form):
        cache.clear()
        response = super().form_valid(form)
        context = self.get_context_data(form=form)
        lesson = self.object
        log.info(
            "Form is valid, creating lesson: %s and context: %s", lesson.id, context
        )
        try:
            task = create_lesson_task.delay(lesson.id)
            time.sleep(2)
        except Exception as e:
            log.error(f"Не получили результата из Celery c ошибкой: {e}")
        # if self.request.htmx:
        res = AsyncResult(task.id, app=current_app)
        context = {
            # "form": form,
            "task_id": task.id,
            # "lesson_id": lesson.id,
            "lesson": lesson,
            "status": res.state,
            # "HX-Trigger": "create_run",
        }
        log.warning("Передаем в форму контекст %s", context)
        response = render(
            self.request,
            self.template_name,
            context,
        )
        # response["HX-Trigger"] = "success"
        response["HX-Trigger"] = "create_run"
        # self.request.session["task_id"] = task.id
        # self.request.session["lesson_id"] = lessn_id
        # return response
        if res.state in ["PENDING", "PROGRESS"]:
            # response["HX-Retarget"] = (
            #     "lessons/partials/task_status.html#task-status-info"
            # )
            # response["HX-Reswap"] = "outerHTML"
            return HttpResponseRedirect(
                reverse_lazy(
                    "lessons:task_status",
                    kwargs={"task_id": task.id},
                )
            )
        else:
            log.warning("Вышли из FormValid")
            return response


# class TaskStatusView(View):
#     def get(self, request, task_id):
@counter
@require_http_methods(["GET"])
def task_status(request: HtmxHttpRequest, task_id) -> HttpResponse:
    global count_status
    count_status += 1
    task_id = request.GET.get("task_id") or task_id
    # lesson = request.GET.get("lesson") or lesson
    # template_name = "lessons/lesson_form.html#task-status-info"
    template_name = "lessons/partials/task_status.html"
    # template_name = "lessons/lesson_list.html"
    if request.htmx:
        log.warning("Итерация %s, task_id: %s", count_status, task_id)
        template_name += "#task-status-info"
        res = AsyncResult(task_id, app=current_app)
    context = {
        "task_id": task_id,
        # "lesson": lesson,
        "task_result": count_status,
        "status": res.state,
    }
    response = render(request, template_name=template_name, context=context)
    if res.state == "SUCCESS":
        count_status = 0
        context["status"] = "SUCCESS"
        response = render(request, template_name=template_name, context=context)
        response["HX-Trigger"] = "success"
        # Очищаем task_id и lesson из сессии когда задача завершена
        request.session.pop("task_id", None)
        # request.session.pop("lesson", None)
        log.warning("Текущий статус: %s и контекст: %s", res.state, context)
        return HttpResponseClientRefresh()
    elif res.state == "FAILURE":
        count_status = 0
        context["status"] = "FAILURE"
        response = render(request, template_name=template_name, context=context)
        response["HX-Trigger"] = "failure"
        # Очищаем task_id и lesson из сессии при ошибке
        request.session.pop("task_id", None)
        # request.session.pop("lesson", None)
        log.warning("Текущий статус: %s и контекст: %s", res.state, context)
        return HttpResponseClientRefresh()
    else:
        response = render(request, template_name=template_name, context=context)
        log.warning("Текущий статус: %s и контекст: %s", res.state, context)
        return response


class LessonCompleteView(UpdateView):
    model = Lesson
    fields = []
    success_url = reverse_lazy("lessons:lesson_list")

    def post(self, request, *args, **kwargs):
        lesson = self.get_object()
        lesson.status = "completed"
        lesson.save()
        return HttpResponseClientRefresh()
