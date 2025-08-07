# Base Python image
FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Set working directory
WORKDIR /app

# Copy backend code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Flask default)
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
