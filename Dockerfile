# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory to /app
WORKDIR /app

# Install system dependencies (needed for Playwright if you enable scraping)
# We include minimal dependencies for the dashboard, add more if scrapers are needed.
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy local code to the container image.
COPY . .

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# (Optional) Install Playwright browsers if needed
# RUN playwright install chromium

# Expose port 8501 for Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the web service on container startup.
# We set PYTHONPATH to include src if needed, but app.py currently handles direct data access.
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
