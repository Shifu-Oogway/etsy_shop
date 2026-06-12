FROM python:3.12-slim

# Exact apt package names matter (e.g. libgdk-pixbuf-2.0-0). Heavy render
# libraries are intentionally NOT system dependencies here.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
