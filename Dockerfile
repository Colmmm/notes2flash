ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

COPY addon /app/addon
COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["python", "addon/bundle_addon.py"]
