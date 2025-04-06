# Use an official Python image with a smaller footprint
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Install Python dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add application code to the Docker image
ADD . /app

# Set environment variables
ENV FLASK_ENV=production
# Set to "development" for development mode
ENV FLASK_APP=server.py
# Flask needs to know the entry point of the app

# Expose the Flask app's port
EXPOSE 5000

# Define the command to run the Flask server
CMD ["python3", "server.py"]
