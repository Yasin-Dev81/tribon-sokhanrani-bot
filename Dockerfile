# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages
RUN pip install -U pip
RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variables
# ENV TELEGRAM_BOT_TOKEN=7005827895:AAEd4wtyF-oOftIoNG0PSV0dK4yGZR7fhek
# ENV BASE_CAPTION="hi man"
# ENV CHANEL_CHAT_ID=-1002218177926
# ENV GROUP_CHAT_ID=-1002218303002

# Run the bot when the container launches
RUN ["python", "migrate.py"]
CMD ["python", "main.py"]
