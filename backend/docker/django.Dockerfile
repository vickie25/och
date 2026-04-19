FROM python:3.11-slim-bookworm

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DEFAULT_TIMEOUT=6000

# Keep system deps minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY backend/django_app/requirements.txt .

# Consolidate pip install: Install critical dependencies then the rest from requirements.txt
# We align Django to 4.2.x as per requirements.txt stability note.
RUN pip install --no-cache-dir --timeout=6000 \
    "pip>=24.0" \
    "setuptools>=69.0.0" \
    "wheel>=0.42.0" \
    && pip install --no-cache-dir --timeout=6000 -r requirements.txt

COPY backend/django_app/ .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
