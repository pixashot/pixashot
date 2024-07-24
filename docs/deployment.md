# Deployment

This guide provides steps to deploy Pixashot to Google Cloud Run using Cloud Build.

## Prerequisites

1. **Google Cloud Account**: Set up a Google Cloud account and create a new project.
2. **Enable APIs**: Enable the following APIs in your Google Cloud project:
    - Cloud Run API
    - Cloud Build API
    - Artifact Registry API
3. **Install Google Cloud SDK**: Install and initialize the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) on your local machine.

## Deployment Steps

1. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Set up Artifact Registry**:
   ```bash
   gcloud artifacts repositories create pixashot-repo --repository-format=docker --location=us-central1
   ```

3. **Use Cloud Build to build and push your Docker image**:
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```

4. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy pixashot-service \
     --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/pixashot-repo/pixashot:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

5. **Access your deployed service**:
   ```bash
   gcloud run services describe pixashot-service --platform managed --region us-central1 --format 'value(status.url)'
   ```

## Automating Deployment

To fully automate the build and deploy process, extend your `cloudbuild.yaml` to include the deployment step.

## Troubleshooting

- Ensure your Google Cloud user account has the necessary roles (e.g., Cloud Run Admin, Cloud Build Editor).
- For Mac M1/M2 users: If you encounter architecture compatibility issues, add this to your Dockerfile:
  ```dockerfile
  FROM --platform=linux/amd64 your-base-image
  ```

For more detailed information, refer to the [official Google Cloud Run documentation](https://cloud.google.com/run/docs).