from celery import shared_task

from .models import Lesson
from itschooltt.utils import log
import time


@shared_task(bind=True)
def create_lesson_task(self, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    log.info("Урок Создан")

    self.update_state(
        state="PROGRESS", meta={"status": "Отправляем уведомления ученикам"}
    )

    students = lesson.get_students_for_notification()
    for student in students:
        log.warning(
            f"Уведомление отправлено студенту c ID[{student.id}] по уроку {lesson.title}"
        )
        time.sleep(1)  # Задержка для симуляции отправки

    lesson.status = "created"
    lesson.save()

    return {"status": "Уведомления отправлены"}
