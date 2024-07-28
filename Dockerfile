FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1
ENV BOT_VERSION="5.1"

WORKDIR /code

COPY ./requirements.txt /code/
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

CMD ["bash", "-c", "alembic upgrade head; python main.py"]
