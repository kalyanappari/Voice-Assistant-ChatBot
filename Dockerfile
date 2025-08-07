# Use official Python image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Copy backend and frontend folders
COPY ./backend /app/backend
COPY ./frontend /app/frontend

# Set environment variables directly (or use GitHub secrets)
ENV GROQ_API_KEY=${groq_api_key}
ENV MODEL_NAME=llama-3-8b-instruct

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Set the working directory to backend
WORKDIR /app/backend

# Expose the port Flask will run on
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
