FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

# Install system deps required for Chromium
RUN apt-get update && apt-get install -y \
    wget gnupg curl xvfb \
    libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
    fonts-liberation libappindicator3-1 libdrm2 libgbm1 \
    libxkbcommon0 xdg-utils && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000

# --- START COMMAND ---
CMD ["uvicorn", "CT_FastAPI:app", "--host", "0.0.0.0", "--port", "8000"]
