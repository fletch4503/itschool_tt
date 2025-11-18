from django.core.management.base import BaseCommand

from faker import Faker

from lessons.models import Course, Group, Student, Teacher, Subject, Lesson


class Command(BaseCommand):
    help = "Populate database with test data"

    def handle(self, *args, **options):
        fake = Faker("ru_RU")

        # Создать курсы
        courses = []
        for _ in range(3):
            course = Course.objects.create(name=fake.sentence(nb_words=3))
            courses.append(course)

        # Предметы
        subjects = []
        for _ in range(5):
            subject = Subject.objects.create(name=fake.sentence(nb_words=2))
            subjects.append(subject)

        # Преподаватели
        teachers = []
        for _ in range(5):
            teacher = Teacher.objects.create(name=fake.name(), email=fake.email())
            teachers.append(teacher)

        # Группы
        groups = []
        for course in courses:
            for _ in range(2):
                group = Group.objects.create(
                    name=fake.word().capitalize(), course=course
                )
                groups.append(group)

        # Студенты
        for group in groups:
            for _ in range(10):
                Student.objects.create(
                    name=fake.name(), email=fake.email(), group=group
                )

        # Уроки
        import random
        from django.utils import timezone

        for _ in range(20):
            scheduled_at = fake.date_time_this_year()
            status = "completed" if scheduled_at < timezone.now() else "pending"
            Lesson.objects.create(
                title=fake.sentence(nb_words=4),
                description=fake.text(),
                subject=random.choice(subjects),
                teacher=random.choice(teachers),
                group=random.choice(groups),
                scheduled_at=scheduled_at,
                status=status,
            )

        self.stdout.write(self.style.SUCCESS("Test data populated"))
