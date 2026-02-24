# Deploying the DAZN Competitive Dashboard

This guide provides instructions for deploying the Streamlit dashboard to various hosting platforms.

## 1. Streamlit Community Cloud (Recommended & Free)
The easiest way to deploy is through Streamlit's official cloud service.

1.  **Sign in**: Go to [share.streamlit.io](https://share.streamlit.io/) and connect your GitHub account.
2.  **Deploy App**: 
    - Select your repository: `logicalninja/dazncomp`
    - Main file path: `app.py`
    - Branch: `main`
3.  **Advanced Settings** (Optional):
    - You can leave the default settings. The files I added in `.streamlit/config.toml` will handle the theme and basic server settings.

## 2. Docker (GCP, AWS, Azure, DigitalOcean)
If you prefer to host it yourself using a containerized service:

1.  **Build the image**:
    ```bash
    docker build -t dazn-dashboard .
    ```
2.  **Run locally**:
    ```bash
    docker run -p 8501:8501 dazn-dashboard
    ```
3.  **Push to Container Registry**: Push to Google Container Registry (GCR), Amazon ECR, or Azure ACR and deploy to their respective App Service or Container Cloud service.

## 3. Persistent Data Note
The dashboard is currently designed to use the static CSV data provided in the `data/` directory. If you want to enable the scraping functionality in the cloud, you will need to:
1. Ensure `playwright` dependencies are installed (see `Dockerfile` comments).
2. Configure a periodic task (like a GitHub Action or Cron job) to run the scrapers and commit the updated data, or use a database.
