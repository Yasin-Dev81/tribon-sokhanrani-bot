FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

ENV BOT_VERSION="4.12"

# Run database migrations
# RUN ["python", "migrate.py", "upgrade"]
# # Define the command to run your application
CMD ["python", "main.py"]
# CMD ["bash", "-c", "alembic upgrade head; python main.py"]
# CMD ["bash", "-c", "alembic upgrade head && alembic --version && python main.py "]
