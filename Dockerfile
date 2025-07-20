FROM python:3.11-slim
WORKDIR /app
COPY src/main.py .
COPY prompt.txt .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]