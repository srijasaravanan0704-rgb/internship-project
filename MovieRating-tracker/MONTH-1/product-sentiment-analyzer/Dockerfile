FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies for headless browser & compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose port
EXPOSE 5000

ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["python", "run.py"]
