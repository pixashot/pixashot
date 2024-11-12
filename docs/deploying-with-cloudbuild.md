# Deploying with Google Cloud Build

This comprehensive guide walks you through deploying Pixashot using Google Cloud Build, from initial setup to advanced configuration and maintenance.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Repository Configuration](#repository-configuration)
4. [Deployment Options](#deployment-options)
5. [Authentication Setup](#authentication-setup)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
8. [Best Practices](#best-practices)
9. [Cost Management](#cost-management)
10. [Additional Resources](#additional-resources)

## Prerequisites

### Google Cloud Account Setup

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

## Initial Setup

### 1. Install Google Cloud SDK

#### Windows Installation
1. Download and install from: [Google Cloud SDK Installation Guide](https://cloud.google.com/sdk/docs/install)
2. Run the installer
3. Open Google Cloud SDK Shell
4. Initialize the SDK:
```bash
gcloud init
```

#### macOS Installation
```bash
# Using Homebrew
brew install --cask google-cloud-sdk

# Initialize the SDK
gcloud init
```

#### Linux Installation
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

### 2. Project Setup

1. **Authentication**
```bash
gcloud auth login
```

2. **Project Management**
```bash
# List existing projects
gcloud projects list

# Create a new project
gcloud projects create YOUR_PROJECT_ID --name="Your Project Name"

# Set active project
gcloud config set project YOUR_PROJECT_ID
```

3. **Enable Required APIs**
```bash
# Enable all required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable iam.googleapis.com

# Verify API enablement
gcloud services list --enabled --filter="name:( \
cloudbuild.googleapis.com \
run.googleapis.com \
artifactregistry.googleapis.com \
storage.googleapis.com \
logging.googleapis.com \
iam.googleapis.com \
)"
```

4. **Configure Cloud Build Service Account Permissions**
```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

# Configure both service accounts with required roles
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin" \
    --role="roles/iam.serviceAccountUser" \
    --role="roles/iam.serviceAccountTokenCreator" \
    --role="roles/run.serviceAgent" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/run.admin" \
    --role="roles/run.serviceAgent" \
    --role="roles/run.invoker"

# Verify role assignments
gcloud projects get-iam-policy $(gcloud config get-value project) \
    --flatten="bindings[].members" \
    --filter="bindings.members:(@cloudbuild.gserviceaccount.com OR @developer.gserviceaccount.com)"
```

5. **Configure Docker Authentication**
```bash
gcloud auth configure-docker
```

## Repository Configuration

### Create Artifact Registry Repository

1. **Create Repository**
```bash
gcloud artifacts repositories create pixashot-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for Pixashot"
```

2. **Verify Creation**
```bash
gcloud artifacts repositories list
```

## Deployment Options

### Configuration Options

| Option | Description | Default | Example Usage |
|--------|-------------|---------|---------------|
| Region | Deployment location | us-central1 | us-east1, europe-west1 |
| Service Name | Cloud Run service name | pixashot | my-pixashot-prod |
| Memory | Container memory | 2Gi | 2Gi, 512Mi |
| CPU | CPU allocation | 1 | 2, 0.5 |
| Min Instances | Minimum running instances | 0 | 1, 2 |
| Max Instances | Maximum running instances | 10 | 5, 20 |
| Port | Container port | 8080 | 3000, 8000 |
| Timeout | Request timeout (seconds) | 300 | 600, 900 |
| Browser Max Contexts | Maximum browser contexts | 15 | 20, 30 |
| Browser Context Timeout | Context timeout (seconds) | 300 | 600, 900 |
| Browser Memory Limit | Memory limit before cleanup (MB) | 1500 | 2000, 3000 |

### Default Configuration

```yaml
_REGION: us-central1
_SERVICE_NAME: pixashot
_REPOSITORY: pixashot-repo
_TAG: latest
_MIN_INSTANCES: "0"
_MAX_INSTANCES: "10"
_MEMORY: "2Gi"
_CPU: "1"
_PORT: "8080"
_TIMEOUT: "300"
_BROWSER_MAX_CONTEXTS: "15"
_BROWSER_CONTEXT_TIMEOUT: "300"
_BROWSER_MEMORY_LIMIT_MB: "1500"
_AUTH_TOKEN: ""
```

### Basic Deployment

Deploy with default settings:
```bash
# Without detailed logging
gcloud builds submit --config cloudbuild.yaml

# With detailed logging
gcloud beta builds submit --config cloudbuild.yaml
```

### Custom Deployment

Override default settings:
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=\
_REGION=us-east1,\
_SERVICE_NAME=my-pixashot,\
_MEMORY=4Gi,\
_CPU=2,\
_MIN_INSTANCES=1,\
_MAX_INSTANCES=5,\
_BROWSER_MAX_CONTEXTS=20,\
_BROWSER_MEMORY_LIMIT_MB=3000,\
_AUTH_TOKEN=$(openssl rand -hex 32)
```

## Authentication Setup

### Cloud Build Service Account Permissions

The Cloud Build service account requires specific IAM roles to deploy and configure Cloud Run services:

| Role | Purpose | Role Name |
|------|---------|-----------|
| Cloud Run Admin | Allows deployment and management of Cloud Run services | `roles/run.admin` |
| Service Account User | Allows Cloud Build to act as service accounts | `roles/iam.serviceAccountUser` |
| Service Account Token Creator | Allows creation of authentication tokens | `roles/iam.serviceAccountTokenCreator` |

If you encounter permissions errors during deployment, verify these roles:

```bash
# List current IAM policies
gcloud projects get-iam-policy $(gcloud config get-value project) \
    --flatten="bindings[].members" \
    --filter="bindings.members:@cloudbuild.gserviceaccount.com"
```

### Configuring Application Authentication

1. **Initial Deployment with Authentication**
```bash
# Generate authentication token
AUTH_TOKEN=$(openssl rand -hex 32)
echo "Your authentication token is: $AUTH_TOKEN"

# Deploy with token
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_AUTH_TOKEN=$AUTH_TOKEN
```

2. **Update Authentication Token**
```bash
# Generate new token
AUTH_TOKEN=$(openssl rand -hex 32)
echo "Your new authentication token is: $AUTH_TOKEN"

# Update service
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_AUTH_TOKEN=$AUTH_TOKEN
```

3. **Using Authentication in Requests**
```bash
curl -X POST https://your-service-url/capture \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Security Notes
- Store authentication tokens in a secure password manager or secrets management system
- Never save tokens in files or version control
- Rotate tokens regularly
- Keep backup access to the service in case of token loss

## Environment Configuration

### Development Environment
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=\
_SERVICE_NAME=pixashot-dev,\
_MEMORY=512Mi,\
_MIN_INSTANCES=0,\
_BROWSER_MAX_CONTEXTS=10,\
_BROWSER_MEMORY_LIMIT_MB=1000,\
_AUTH_TOKEN=$AUTH_TOKEN
```

### Production Environment
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=\
_SERVICE_NAME=pixashot-prod,\
_MEMORY=4Gi,\
_MIN_INSTANCES=1,\
_BROWSER_MAX_CONTEXTS=20,\
_BROWSER_MEMORY_LIMIT_MB=3000,\
_AUTH_TOKEN=$AUTH_TOKEN
```

### Performance-Optimized Configuration
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=\
_MEMORY=8Gi,\
_CPU=4,\
_MIN_INSTANCES=2,\
_MAX_INSTANCES=10,\
_BROWSER_MAX_CONTEXTS=30,\
_BROWSER_MEMORY_LIMIT_MB=6000,\
_BROWSER_CONTEXT_TIMEOUT=600,\
_AUTH_TOKEN=$AUTH_TOKEN
```

## Monitoring and Troubleshooting

### Viewing Logs

1. **Build Logs**
```bash
gcloud builds log [BUILD_ID]
```

2. **Service Logs**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=my-pixashot" --limit=50
```

3. **List Recent Builds**
```bash
gcloud builds list
```

### Common Issues and Solutions

1. **Permission Issues**
- Verify Cloud Build service account roles
- Ensure proper IAM bindings
- Check service account permissions

2. **Container Startup Issues**
- Check service logs for startup errors
- Verify environment variables
- Review health check configuration
- Check browser context initialization logs

3. **Memory Issues**
- Adjust `BROWSER_MEMORY_LIMIT_MB`
- Monitor memory usage through logs
- Consider increasing container memory
- Review context cleanup logs

4. **Performance Issues**
- Adjust `BROWSER_MAX_CONTEXTS`
- Monitor context reuse rates
- Check context timeout settings
- Consider increasing CPU allocation

## Best Practices

### Security
- Use HTTPS exclusively
- Implement proper authentication
- Rotate credentials regularly
- Review access permissions
- Monitor security logs

### Performance
- Start with recommended resources
- Monitor metrics
- Adjust based on usage patterns
- Use minimum instances strategically
- Optimize browser context settings

### Version Management
- Use meaningful tags
- Implement versioning strategy
- Track successful configurations
- Document deployment changes

## Cost Management

### Free Tier Optimization
- Monitor credit usage
- Set up billing alerts
- Understand free tier limits
- Track usage patterns

### Resource Optimization
- Use minimum instances of 0 when possible
- Scale based on actual usage
- Monitor and optimize resource allocation
- Review cost reports regularly
- Optimize browser context settings for efficiency

## Additional Resources

- [Google Cloud Free Tier](https://cloud.google.com/free)
- [Google Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [Google Cloud SDK Reference](https://cloud.google.com/sdk/docs/references)