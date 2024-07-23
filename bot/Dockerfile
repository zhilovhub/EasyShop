FROM python:3.10

WORKDIR /bot

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /

CMD ["python3", "-m", "bot.main"]
