# content-processor/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install required libraries
RUN pip install --no-cache-dir requests

# Copy the content processor script
COPY process_notes.py .

CMD ["python", "process_notes.py"]
