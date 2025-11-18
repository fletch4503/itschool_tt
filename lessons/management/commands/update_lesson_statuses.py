from django.core.management.base import BaseCommand
from django.utils import timezone
from lessons.models import Lesson


class Command(BaseCommand):
    help = "Update lesson statuses based on scheduled_at date"

    def handle(self, *args, **options):
        now = timezone.now()
        updated_count = 0

        # Обновить завершенные занятия
        completed_lessons = Lesson.objects.filter(scheduled_at__lt=now).exclude(
            status="completed"
        )
        for lesson in completed_lessons:
            lesson.status = "completed"
            lesson.save()
            updated_count += 1

        # Обновить ожидающие занятия
        pending_lessons = Lesson.objects.filter(scheduled_at__gte=now).exclude(
            status="pending"
        )
        for lesson in pending_lessons:
            lesson.status = "pending"
            lesson.save()
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Updated {updated_count} lesson statuses")
        )
