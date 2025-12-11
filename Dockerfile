# Playwright base image with Chromium, Firefox, WebKit
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy backend code
COPY . .

EXPOSE 8080

# Start FastAPI with uvicorn (fixed port)
CMD ["uvicorn", "src.MultiBroker_Router:app", "--host", "0.0.0.0", "--port", "8080"]
