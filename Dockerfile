FROM python:3.11-alpine

   # Install system dependencies needed for Python packages
   RUN apk add --no-cache gcc musl-dev linux-headers

   # Set working directory
   WORKDIR /opt/claude-api

   # Copy application code
   COPY main.py .

   # Install Python dependencies
   RUN pip install --no-cache-dir \
       fastapi \
       uvicorn \
       pydantic \
       claude-agent-sdk

   # Expose the port the app runs on
   EXPOSE 3001

   # Set environment variables
   ENV PYTHONUNBUFFERED=1

   # Run the application
   CMD ["python3", "main.py"]
