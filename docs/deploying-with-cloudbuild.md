# Deploying with Google Cloud Build

This guide provides detailed instructions for deploying Pixashot using Google Cloud Build and the provided `cloudbuild.yaml` configuration.

## Prerequisites

### 1. Google Cloud Account Setup

Before you begin, you'll need a Google Cloud account. Here's how to get started:

1. **Sign up for Google Cloud**
   - Visit [cloud.google.com](https://cloud.google.com)
   - Click "Get started for free"
   - New customers receive $300 in free credits valid for 90 days

2. **Complete Registration**
   - Select your country of residence
   - Accept the Terms of Service
   - Fill out the registration form
   - Provide payment details for verification
     - A small verification charge will be made (refundable within 2-3 days)
     - Payment verification is required even for free tier
     - Enable automatic payments to avoid service interruptions

3. **Free Tier Benefits**
   - $300 initial credit valid for 90 days
   - Access to 20+ products with free tier limits
   - Free tier usage does not expire (subject to limits)
   - Includes:
     - Compute Engine (1 e2-micro instance per month)
     - Cloud Functions (2 million invocations)
     - Various AI and ML services

### 2. Install Google Cloud SDK

#### For Windows:
1. Download and install from: [Google Cloud SDK Installation Guide](https://cloud.google.com/sdk/docs/install)
2. Run the installer
3. Open Google Cloud SDK Shell
4. Initialize the SDK:
   ```bash
   gcloud init
   ```

#### For macOS:
```bash
# Using Homebrew
brew install --cask google-cloud-sdk

# Initialize the SDK
gcloud init
```

#### For Linux:
```bash
# Add Google Cloud SDK distribution URI as a package source
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import the Google Cloud public key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Update and install the SDK
sudo apt-get update && sudo apt-get install google-cloud-sdk

# Initialize the SDK
gcloud init
```

### 3. Initial Project Setup

1. **Log in to Google Cloud**
   ```bash
   gcloud auth login
   ```
   Follow the browser prompts to authenticate your account.

2. **Project Management**
   ```bash
   # List existing projects
   gcloud projects list

   # Create a new project (optional)
   gcloud projects create YOUR_PROJECT_ID --name="Your Project Name"

   # Set your active project
   gcloud config set project YOUR_PROJECT_ID

   # Verify selected project
   gcloud config get-value project
   ```
   Replace `YOUR_PROJECT_ID` with your desired project ID. Project IDs must be:
   - Between 6 and 30 characters
   - Contain only lowercase letters, numbers, and hyphens
   - Start with a letter
   - Be globally unique across Google Cloud

### 4. Enable Required APIs

After setting up your project, enable the necessary APIs:

1. **Enable Core Services**
   ```bash
   # Enable required APIs for the project
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

2. **Verify API Enablement**
   ```bash
   # List enabled APIs
   gcloud services list --enabled

   # Check status of specific API
   gcloud services list --enabled --filter="name:( cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com )"
   ```

### 5. Configure Docker Authentication

```bash
gcloud auth configure-docker
```

## Creating the Artifact Registry Repository

1. **Create a repository**:
   ```bash
   gcloud artifacts repositories create pixashot-repo \
       --repository-format=docker \
       --location=us-central1 \
       --description="Docker repository for Pixashot"
   ```

2. **Verify repository creation**:
   ```bash
   gcloud artifacts repositories list
   ```

## Cloud Build Configuration

The project includes a `cloudbuild.yaml` file ([view file](../cloudbuild.yaml)) that handles the build and deployment process. Here are the key configuration options you can customize:

### Important Configuration Options

| Option | Description | Default | Example Usage |
|--------|-------------|---------|---------------|
| Region | Deployment location | us-central1 | us-east1, europe-west1 |
| Service Name | Cloud Run service name | pixashot | my-pixashot-prod |
| Memory | Container memory | 1Gi | 2Gi, 512Mi |
| CPU | CPU allocation | 1 | 2, 0.5 |
| Min Instances | Minimum running instances | 0 | 1, 2 |
| Max Instances | Maximum running instances | 10 | 5, 20 |
| Port | Container port | 8080 | 3000, 8000 |
| Timeout | Request timeout (seconds) | 300 | 600, 900 |

### Basic Deployment

Deploy with default settings and required Cloud Run configuration:
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_CLOUDBUILD_ENV_VARS="CLOUD_RUN=true"
```

### Custom Deployment

Override default settings:
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=\
_REGION=us-east1,\
_SERVICE_NAME=my-pixashot,\
_MEMORY=2Gi,\
_CPU=2,\
_MIN_INSTANCES=1,\
_MAX_INSTANCES=5,\
_CLOUDBUILD_ENV_VARS="CLOUD_RUN=true"
```

### Environment-Specific Deployment

For different environments:

```bash
# Development
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=\
_SERVICE_NAME=pixashot-dev,\
_MEMORY=512Mi,\
_MIN_INSTANCES=0,\
_CLOUDBUILD_ENV_VARS="CLOUD_RUN=true"

# Production
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=\
_SERVICE_NAME=pixashot-prod,\
_MEMORY=2Gi,\
_MIN_INSTANCES=1,\
_CLOUDBUILD_ENV_VARS="CLOUD_RUN=true"
```

### Important Note

The `CLOUD_RUN` environment variable should be set to `true` when deploying to Cloud Run. This ensures proper container initialization and user permissions handling. The examples above include this setting through the `_CLOUDBUILD_ENV_VARS` substitution.

## Post-Deployment Configuration

1. **Set environment variables**:
   ```bash
   gcloud run services update my-pixashot \
     --region=us-central1 \
     --set-env-vars=AUTH_TOKEN=your_secure_token,RATE_LIMIT_ENABLED=true
   ```

2. **View service URL**:
   ```bash
   gcloud run services describe my-pixashot \
     --region=us-central1 \
     --format='value(status.url)'
   ```

## Monitoring and Troubleshooting

1. **View build logs**:
   ```bash
   gcloud builds log [BUILD_ID]
   ```

2. **List recent builds**:
   ```bash
   gcloud builds list
   ```

3. **View service logs**:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=my-pixashot" --limit=50
   ```

## Common Issues and Solutions

1. **Permission Errors**
   - Ensure your account has the necessary roles:
     ```bash
     gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member=user:your-email@example.com \
       --role=roles/run.admin
     
     gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member=user:your-email@example.com \
       --role=roles/cloudbuild.builds.editor
     ```

2. **Build Failures**
   - Check build logs for detailed error messages
   - Verify your cloudbuild.yaml syntax
   - Ensure all required APIs are enabled

3. **Deployment Timeouts**
   - Increase the timeout value in your substitutions
   - Check resource allocations

4. **Container Startup Issues**
   - View service logs for startup errors
   - Verify environment variables are set correctly
   - Check container health checks

## Best Practices

1. **Version Management**
   - Use meaningful tags for your deployments
   - Consider implementing a versioning strategy
   - Keep track of successful configurations

2. **Resource Optimization**
   - Start with the recommended resources and adjust based on usage
   - Monitor performance metrics
   - Use minimum instances wisely to balance cost and performance

3. **Security**
   - Always use HTTPS
   - Implement proper authentication
   - Regularly rotate credentials
   - Review and audit access permissions

4. **Monitoring**
   - Set up alerts for critical metrics
   - Monitor costs and usage
   - Regularly review logs for issues

## Cost Management

1. **Free Tier Usage**
   - Monitor your free credit usage through the billing dashboard
   - Set up billing alerts to avoid unexpected charges
   - Understand which services are free tier eligible

2. **Cost Optimization**
   - Use minimum instances of 0 when possible
   - Scale resources based on actual usage
   - Monitor and optimize resource allocation

## Additional Resources

- [Google Cloud Free Tier](https://cloud.google.com/free)
- [Google Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [Google Cloud SDK Reference](https://cloud.google.com/sdk/docs/references)