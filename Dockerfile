# Use lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (hugging face uses 7860)
EXPOSE 7860

# Use gunicorn to run Flask on port 7860
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
