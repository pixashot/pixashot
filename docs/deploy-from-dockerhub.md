# Deploying Pixashot to Google Cloud Run

This guide walks you through the process of deploying the Pixashot service to Google Cloud Run directly from Docker Hub. For more detailed information on Cloud Run deployments, refer to the [official Google Cloud Run deployment documentation](https://cloud.google.com/run/docs/deploying).

## Prerequisites

- A Google Cloud account with billing enabled
- Google Cloud CLI installed (optional, but recommended)
- Basic familiarity with Google Cloud Console

## Deployment Steps

1. **Access Google Cloud Console**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Navigate to Cloud Run**
   - In the left sidebar, go to "Cloud Run"
   - Click "Create Service"

3. **Configure the Service**
   - For "Container image URL", enter: `gpriday/pixashot:latest`
   - Choose a service name (e.g., "pixashot-service")
   - Select a region for deployment

4. **Set Resources**
   - Under "CPU allocation and pricing", select "CPU is only allocated during request processing"
   - Set CPU to 1
   - Set Memory to 1 GiB

5. **Configure Concurrency**
   - Expand the "Container(s), Networking, Security" section
   - Find "Maximum concurrent requests per instance" and set it to a value between 4 and 8
   - This setting allows each instance to handle multiple requests simultaneously, improving efficiency

6. **Configure Authentication**
   - Under "Authentication", select "Allow unauthenticated invocations"
   - This allows public access to your service, but you'll use the `AUTH_TOKEN` for application-level authentication

7. **Set Environment Variables**
   - Click on "Variables & Secrets" to expand the section
   - Click "Add Variable"
   - Set the variable name to `AUTH_TOKEN`
   - Set the value to a strong, unique string that you'll keep private
   - This token will be used for authenticating requests to your service

8. **Configure Autoscaling**
   - Under "Autoscaling", set minimum instances to 0 and maximum instances to your desired limit (e.g., 10)
   - Note: Setting minimum instances to 1 will prevent cold starts but increase costs. Setting it to 0 is recommended to keep costs down, especially for low-traffic services.

9. **Review and Create**
   - Review all settings
   - Click "Create" at the bottom of the page

10. **Access Your Service**
    - Once deployment is complete, you'll see a URL for your service
    - To use the service, include your `AUTH_TOKEN` in the `Authorization` header of your requests:
      ```
      Authorization: Bearer YOUR_AUTH_TOKEN
      ```

## Authentication Options

1. **Allow unauthenticated invocations (Recommended for Pixashot)**
   - This option allows public access to your service URL
   - Use the `AUTH_TOKEN` environment variable as your primary method of authentication
   - Include the token in the `Authorization` header of all requests to your service

2. **Require authentication**
   - If you prefer to use Google Cloud's built-in authentication:
     - Select "Require authentication" instead of "Allow unauthenticated invocations"
     - Refer to Google's documentation on [authenticating service-to-service requests](https://cloud.google.com/run/docs/authenticating/service-to-service) for details on how to authenticate requests to your service
   - Note: If you choose this option, you'll need to handle both Google Cloud authentication and your `AUTH_TOKEN` in your requests

## Important Notes

- Keep your `AUTH_TOKEN` private and secure. Do not share it publicly.
- The suggested configuration (1 CPU, 1 GB memory) is suitable for most users. Adjust as needed based on your specific requirements.
- Setting "Maximum concurrent requests per instance" to 4-8 allows for efficient handling of multiple requests, but you may need to adjust this based on your specific workload and performance requirements.
- Consider the trade-off between cost and performance when setting minimum instances:
  - 0 instances: Lowest cost, but may experience cold starts
  - 1 instance: Higher cost, but eliminates cold starts and provides faster response times

## Monitoring and Management

- Use the Google Cloud Console to monitor your service's performance, logs, and metrics.
- You can update your service, rollback to previous versions, or adjust settings through the Cloud Run interface in the console.

By following these steps, you'll have Pixashot running on Google Cloud Run, ready to capture screenshots on demand. Remember to secure your `AUTH_TOKEN` and manage your service's access carefully.

For more advanced configurations and best practices, refer to the [Google Cloud Run documentation](https://cloud.google.com/run/docs).