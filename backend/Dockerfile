FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY app.py excel_exporter.py testcase_generator.py ./
COPY template ./template
RUN mkdir -p data
EXPOSE 5000
CMD ["python", "app.py"]
