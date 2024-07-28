FROM python:3.10-slim

ENV BOT_VERSION="5.3"

WORKDIR /code

COPY ./requirements.txt /code/
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

# RUN alembic upgrade head
CMD ["python", "main.py"]
# CMD ["bash", "-c", "alembic upgrade head && python main.py"]
# CMD ["bash", "-c", "alembic upgrade head;", "python main.py"]
