from celery import shared_task

from .models import Lesson
from itschooltt.utils import log
import time


@shared_task(bind=True)
# @shared_task(name="Create_lesson_task", ignore_result=False)
def create_lesson_task(self, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    log.info("Урок Создан под номером %s", lesson_id)
    self.update_state(
        state="PROGRESS", meta={"status": "Отправляем уведомления ученикам"}
    )
    students = lesson.get_students_for_notification()
    log.info("Длина списка студентов %s, к уроку %s", len(students), lesson_id)
    for student in students:
        log.warning(
            f"Уведомление отправлено студенту c ID[{student.id}] по уроку {lesson.title}"
        )
        time.sleep(2)  # Задержка для симуляции отправки
    lesson.status = "created"
    lesson.save()

    return {"status": "Уведомления отправлены"}
