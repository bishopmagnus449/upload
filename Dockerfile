FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . /app/

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python3", "main.py"]