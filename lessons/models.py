from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="groups")

    def __str__(self):
        return f"{self.name} ({self.course.name})"


class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="students")

    def __str__(self):
        return self.name


class Teacher(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Lesson(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("created", "Создан"),
        ("completed", "Завершен"),
    ]
    title = models.CharField(max_length=200, verbose_name="Урок:")
    description = models.TextField(verbose_name="Описание Урока:")
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, verbose_name="Предмет:"
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель:"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Группа Студентов:",
    )
    students = models.ManyToManyField(Student, blank=True, verbose_name="Студенты:")
    scheduled_at = models.DateTimeField(
        default="2026-02-12 12:00", verbose_name="Запланировано на:"
    )  # Только для примера задано значение по умолчанию
    duration = models.DurationField(
        default="01:00:00", verbose_name="Длительность урока:"
    )  # Длительность урока по умолчанию 1 час
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Урок:")

    def __str__(self):
        return self.title

    def get_students_for_notification(self):
        if self.group:
            return self.group.students.all()
        return self.students.all()
