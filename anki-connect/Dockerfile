# anki-connect-service/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install required libraries
RUN pip install --no-cache-dir requests

# Install curl
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the Anki Connect script
COPY add_to_anki.py .

CMD ["python", "add_to_anki.py"]