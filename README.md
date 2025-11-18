# IT School Test Task

Django-приложение для управления уроками в школе.

## Функционал

- Модели: Course, Group, Student, Teacher, Subject, Lesson
- Создание уроков с асинхронной рассылкой уведомлений студентам через Celery
- HTMX для обновления интерфейса без JS
- Цветное логирование
- Docker для развертывания

## Установка и запуск

### С использованием Docker (рекомендуется)

1. Установите Docker и Docker Compose.

2. Клонируйте репозиторий.

3. Запустите сервисы:

   ```bash
   docker-compose up --build -d
   ```

4. При первом запуске примените миграции и заполните тестовыми данными:

   ```bash
   docker-compose exec web uv run python manage.py migrate
   docker-compose exec web uv run python manage.py populate_data
   ```

5. Откройте http://localhost:8000

### Локальная установка

1. Установите uv: `pip install uv`

2. Синхронизируйте зависимости: `uv sync`

3. Настройте PostgreSQL и Redis локально.

4. Установите переменные окружения (DB_HOST, etc.)

5. Запустите:

   ```bash
   uv run python manage.py migrate
   uv run python manage.py populate_data
   uv run python manage.py runserver
   uv run celery -A itschooltt worker --loglevel=info
   ```

## Архитектура

- PostgreSQL: база данных
- Redis: кэш и брокер сообщений для Celery
- Celery: асинхронные задачи
- Django + HTMX: веб-интерфейс

## Команды

- `uv run python manage.py populate_data` - заполнить тестовыми данными
- `uv run celery -A itschooltt worker --loglevel=info` - запустить Celery worker
- `uv run python manage.py runserver` - запустить сервер разработки
