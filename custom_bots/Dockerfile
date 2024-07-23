FROM python:3.10

WORKDIR /custom_bots

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /

EXPOSE 88
EXPOSE 7532

CMD ["python3", "-m", "custom_bots.multibot"]
