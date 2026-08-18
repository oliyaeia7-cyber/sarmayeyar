FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# وابستگی‌های سیستمی موردنیاز برای pandas/numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# مسیر ذخیره‌سازی پایگاه‌داده SQLite (در Render به یک Persistent Disk متصل می‌شود)
RUN mkdir -p /app/data

# Render مقدار PORT را در زمان اجرا تزریق می‌کند
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
