# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libappindicator1 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    chromium-driver \
    chromium \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Set environment variables for Selenium and Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your app
COPY . /app
WORKDIR /app

# Expose the Streamlit port
EXPOSE 8501

# IMPORTANT: Use environment variable for Cloud Run port
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0

