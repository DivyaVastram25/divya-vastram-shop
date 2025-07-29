# Use a base image with Python
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask runs on
EXPOSE 7860

# Set environment variable
ENV FLASK_APP=app.py

# Run the app
CMD ["flask", "run", "--host=0.0.0.0", "--port=7860"]
