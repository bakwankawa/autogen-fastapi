# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Install cron
RUN apt-get update && apt-get install -y cron

# Create a cron file with the desired job
RUN echo "10 14 * * * PYTHONPATH=/usr/src/app /usr/local/bin/python /usr/src/app/app/cron_job.py >> /var/log/cron.log 2>&1" > /etc/cron.d/mycron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/mycron

# Apply the cron job to the crontab
RUN crontab /etc/cron.d/mycron

# Ensure the cron daemon runs in the foreground alongside your main application
CMD cron && PYTHONPATH=./ python app/main.py