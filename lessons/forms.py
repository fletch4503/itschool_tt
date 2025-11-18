from django import forms
from django.forms.widgets import DateTimeInput, TimeInput
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
            "duration",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Название урока"}),
            "description": forms.Textarea(attrs={"placeholder": "Описание урока"}),
            "scheduled_at": DateTimeInput(
                attrs={"type": "datetime-local", "placeholder": "Выберите дату и время"}
            ),
            "duration": TimeInput(
                attrs={"type": "time-local", "placeholder": "Выберите продолжительность"}
            ),
        }
