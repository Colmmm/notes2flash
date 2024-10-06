# google-docs-scraper/Dockerfile
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install required libraries for Google Docs API
RUN pip install --no-cache-dir google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Copy the script and service account file (if needed)
COPY scrape.py .
COPY service_account.json /app/service_account.json 

# Set environment variables for Google Doc ID and service account file
ENV GOOGLE_DOC_ID=${GOOGLE_DOC_ID}
ENV SERVICE_ACCOUNT_FILE=/app/service_account.json

# Command to run the script
CMD ["python", "scrape.py"]
