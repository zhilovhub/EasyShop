FROM python:3.10

WORKDIR /api

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /

EXPOSE 3024

CMD ["python3", "-m", "api.main"]
