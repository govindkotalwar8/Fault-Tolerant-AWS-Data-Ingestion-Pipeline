FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline.py pipeline.py

CMD ["python", "pipeline.py"]
