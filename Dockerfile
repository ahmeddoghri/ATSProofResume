FROM python:3.9-slim

WORKDIR /app

# Install Chrome and dependencies for Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome options to run in container
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# Disable Selenium Manager (use system-installed chromedriver instead)
ENV SE_DISABLE_MANAGER=true

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test scripts and run them
COPY test_deps.py test_imports.py ./
# Skip app modules during build phase
ENV SKIP_APP_MODULES=true
RUN python test_deps.py && python test_imports.py

# Copy application code
COPY . .
RUN python docker_pillow_fix.py
RUN python docker_selenium_fix.py

# Create output directory
RUN mkdir -p output

# Expose the port
EXPOSE 8000

# Add this after copying the application code
ENV PYTHONPATH=/app
# Now we can test with app modules
ENV SKIP_APP_MODULES=false

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 