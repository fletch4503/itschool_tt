from django.core.management.base import BaseCommand
from faker import Faker
from lessons.models import Course, Group, Student, Teacher, Subject, Lesson
from django.utils import timezone
import random


class Command(BaseCommand):
    help = "Create test data based on existing database data"

    def handle(self, *args, **options):
        fake = Faker("ru_RU")

        # Получить существующие данные
        existing_courses = list(Course.objects.all())
        existing_subjects = list(Subject.objects.all())
        existing_teachers = list(Teacher.objects.all())
        existing_groups = list(Group.objects.all())
        existing_students = list(Student.objects.all())
        existing_lessons = list(Lesson.objects.all())

        if not existing_courses:
            self.stdout.write(
                self.style.WARNING(
                    "No existing courses found. Run populate_data first."
                )
            )
            return

        # Создать дополнительные курсы на основе существующих
        for course in existing_courses:
            for _ in range(2):
                Course.objects.create(
                    name=f"{course.name} - {fake.word().capitalize()}"
                )

        # Создать дополнительные предметы
        for subject in existing_subjects:
            for _ in range(3):
                Subject.objects.create(name=f"{subject.name} ({fake.word()})")

        # Создать дополнительных преподавателей
        for teacher in existing_teachers:
            for _ in range(2):
                Teacher.objects.create(
                    name=fake.name(), email=f"{fake.user_name()}@{fake.domain_name()}"
                )

        # Обновить списки
        all_courses = list(Course.objects.all())
        all_subjects = list(Subject.objects.all())
        all_teachers = list(Teacher.objects.all())

        # Создать дополнительные группы
        for course in all_courses:
            existing_groups_for_course = [
                g for g in existing_groups if g.course == course
            ]
            for _ in range(2):
                Group.objects.create(
                    name=f"{fake.word().capitalize()} {len(Group.objects.filter(course=course)) + 1}",
                    course=course,
                )

        # Обновить группы
        all_groups = list(Group.objects.all())

        # Создать дополнительных студентов
        for group in all_groups:
            existing_students_in_group = [
                s for s in existing_students if s.group == group
            ]
            for _ in range(5):
                Student.objects.create(
                    name=fake.name(), email=fake.email(), group=group
                )

        # Обновить студентов
        all_students = list(Student.objects.all())

        # Создать дополнительные уроки
        for _ in range(50):
            scheduled_at = fake.date_time_this_year()
            status = "completed" if scheduled_at < timezone.now() else "pending"
            duration = timezone.timedelta(hours=random.randint(1, 3))  # 1-3 часа

            lesson = Lesson.objects.create(
                title=f"{random.choice(all_subjects).name} - {fake.sentence(nb_words=3)}",
                description=fake.text(),
                subject=random.choice(all_subjects),
                teacher=random.choice(all_teachers),
                group=random.choice(all_groups),
                scheduled_at=scheduled_at,
                duration=duration,
                status=status,
            )

            # Добавить случайных студентов
            students_to_add = random.sample(all_students, random.randint(5, 15))
            lesson.students.set(students_to_add)

        self.stdout.write(
            self.style.SUCCESS("Test data created based on existing data")
        )
