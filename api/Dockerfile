FROM python:3.10

WORKDIR /api

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /

EXPOSE 2024

CMD ["uvicorn", "api.main:app", "--host",  "0.0.0.0", "--port", "2024", "--log-level", "info"]
