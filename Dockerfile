# Dockerfile
FROM python:3.12-slim

# Install system dependencies for mysqlclient compilation
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY atp_admin_ui/ .

EXPOSE 8001

CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]