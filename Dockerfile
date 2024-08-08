FROM python:3.10-slim

ENV BOT_VERSION="6.8"

WORKDIR /code

COPY ./requirements.txt /code/
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

# RUN alembic upgrade head
CMD ["python", "main.py"]
# CMD ["bash", "-c", "pybabel compile -d locales -D bot; wait-for-it -s $DB_ADDRESS:3306; alembic upgrade head; python main.py"]
