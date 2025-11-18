from celery import shared_task

from .models import Lesson

import logging
import time

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def create_lesson_task(self, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    logger.info("Урок Создан")

    self.update_state(
        state="PROGRESS", meta={"status": "Отправляем уведомления ученикам"}
    )

    students = lesson.get_students_for_notification()
    for student in students:
        logger.info(
            f"Уведомление отправлено студенту {student.id} по уроку {lesson.title}"
        )
        time.sleep(1)  # Задержка для симуляции отправки

    lesson.status = "created"
    lesson.save()

    return {"status": "Уведомления отправлены"}
