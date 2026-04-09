FROM python:3.12-slim-bookworm

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DEFAULT_TIMEOUT=6000

# Keep system deps minimal to avoid OOM during apt on small VPS.
# We use psycopg2-binary, so we don't need build tooling like gcc/python3-dev/libpq-dev here.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY backend/django_app/requirements.txt .

RUN pip install --no-cache-dir --timeout=6000 \
    "Django>=5.0,<6.0" \
    "psycopg2-binary>=2.9.9" \
    "djangorestframework>=3.14.0" \
    "django-environ>=0.10.0" \
    "Pillow>=10.0.0"

RUN pip install --no-cache-dir --timeout=6000 -r requirements.txt

COPY backend/django_app/ .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
