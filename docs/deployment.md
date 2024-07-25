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

## Configuring Rate Limiting

Pixashot supports rate limiting to prevent abuse and ensure fair usage of the service. You can configure rate limiting using environment variables:

1. **Enable rate limiting**:
   Set the `RATE_LIMIT_ENABLED` environment variable to `true`:
   ```bash
   gcloud run services update pixashot-service \
     --set-env-vars RATE_LIMIT_ENABLED=true
   ```

2. **Set rate limit**:
   Configure the rate limit using the `RATE_LIMIT_CAPTURE` environment variable. For example, to set a limit of 10 requests per minute:
   ```bash
   gcloud run services update pixashot-service \
     --set-env-vars RATE_LIMIT_CAPTURE="10 per minute"
   ```

   You can adjust the rate limit as needed, using formats like "1 per second", "100 per hour", etc.

3. **Apply both settings at once**:
   You can set multiple environment variables in a single command:
   ```bash
   gcloud run services update pixashot-service \
     --set-env-vars RATE_LIMIT_ENABLED=true,RATE_LIMIT_CAPTURE="10 per minute"
   ```

Remember to adjust these settings based on your specific requirements and the expected load on your service.

## Automating Deployment

To fully automate the build and deploy process, extend your `cloudbuild.yaml` to include the deployment step.

## Troubleshooting

- Ensure your Google Cloud user account has the necessary roles (e.g., Cloud Run Admin, Cloud Build Editor).
- For Mac M1/M2 users: If you encounter architecture compatibility issues, add this to your Dockerfile:
  ```dockerfile
  FROM --platform=linux/amd64 your-base-image
  ```

For more detailed information, refer to the [official Google Cloud Run documentation](https://cloud.google.com/run/docs).