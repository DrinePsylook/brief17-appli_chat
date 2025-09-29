FROM python:3.12-slim

WORKDIR /app

ENV DJANGO_SETTINGS_MODULE=mychat.settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "mychat.asgi:application"]