# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Environment variables should be passed at runtime, for example:
# docker run -p 8000:8000 --env-file .env my-fastapi-app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

