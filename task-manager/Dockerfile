FROM python:3.9-slim

WORKDIR /app

RUN pip install requests prometheus-client

COPY . .

CMD ["python", "task_manager.py"]
