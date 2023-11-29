FROM python:3.11.6-slim

ADD . /app

WORKDIR /app

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 3000

CMD ["python", "main.py"]