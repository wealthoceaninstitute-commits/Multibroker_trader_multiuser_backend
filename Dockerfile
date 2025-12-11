FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install browser binaries
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8080

CMD ["uvicorn", "MultiBroker_Router:app", "--host", "0.0.0.0", "--port", "8080"]
