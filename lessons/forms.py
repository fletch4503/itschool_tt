from django import forms
from django.forms.widgets import DateTimeInput
from .models import Lesson


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "subject",
            "teacher",
            "group",
            "students",
            "scheduled_at",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Название урока"}),
            "description": forms.Textarea(attrs={"placeholder": "Описание урока"}),
            "scheduled_at": DateTimeInput(
                attrs={"type": "datetime-local", "placeholder": "Выберите дату и время"}
            ),
        }
