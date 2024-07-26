# Deployment

This guide provides steps to deploy Pixashot to Google Cloud Run using Cloud Build. You can also deploy to Google Cloud Run directly from Docker Hub by following [this guide](deploy-from-dockerhub.md).

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

## Configuring Environment Variables

Pixashot supports various configuration options through environment variables. You can set these when deploying to Cloud Run:

### Rate Limiting

1. **Enable rate limiting**:
   ```bash
   gcloud run services update pixashot-service \
     --set-env-vars RATE_LIMIT_ENABLED=true
   ```

2. **Set rate limit**:
   ```bash
   gcloud run services update pixashot-service \
     --set-env-vars RATE_LIMIT_CAPTURE="10 per minute"
   ```

### Proxy Configuration

You can set default proxy settings using environment variables:

```bash
gcloud run services update pixashot-service \
  --set-env-vars PROXY_SERVER=proxy.example.com,PROXY_PORT=8080,PROXY_USERNAME=user,PROXY_PASSWORD=pass
```

These proxy settings will be used as defaults if not overridden in individual requests.

### Applying Multiple Settings

You can set multiple environment variables in a single command:

```bash
gcloud run services update pixashot-service \
  --set-env-vars RATE_LIMIT_ENABLED=true,RATE_LIMIT_CAPTURE="10 per minute",PROXY_SERVER=proxy.example.com,PROXY_PORT=8080
```

Remember to adjust these settings based on your specific requirements and the expected load on your service.

## Troubleshooting

- Ensure your Google Cloud user account has the necessary roles (e.g., Cloud Run Admin, Cloud Build Editor).
- For Mac M1/M2 users: If you encounter architecture compatibility issues, add this to your Dockerfile:
  ```dockerfile
  FROM --platform=linux/amd64 your-base-image
  ```

For more detailed information, refer to the [official Google Cloud Run documentation](https://cloud.google.com/run/docs).