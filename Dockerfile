
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    libgl1-mesa-glx \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements_deploy.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements_deploy.txt

# Copy the rest of the application code into the container
# We'll use .dockerignore to skip unnecessary files
COPY . .

# Expose the ports for Streamlit and ZMQ
EXPOSE 8501
EXPOSE 5555

# Set environment variables
ENV PYTHONPATH="/app/fleet-dashboard:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1

# Change to the dashboard directory
WORKDIR /app/fleet-dashboard

# Run the streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
