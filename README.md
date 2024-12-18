# 📸 Pixashot: High-Performance Web Screenshot Service

Pixashot is a reliable, production-ready web screenshot service that captures pixel-perfect screenshots with extensive
customization options. Built with modern browser automation using Playwright and designed for stability and performance,
it's suitable for automated testing, content archival, visual monitoring, and various production use cases.

**Note**: Pixashot is actively developed and continuously improving. Check our [public roadmap](ROADMAP.md) for upcoming
features and enhancements.

## ✨ Key Features

### Core Capabilities

- 🎯 **Pixel-Perfect Capture**: High-fidelity screenshots at any resolution, including Retina displays
- 🌐 **Full Page Support**: Intelligent capture of scrollable content with dynamic height detection
- 📱 **Device Simulation**: Accurate mobile and desktop viewport emulation with customizable settings
- 🎨 **Multiple Formats**: PNG, JPEG, WebP, PDF, and HTML output options
- 🔄 **Dynamic Content**: Smart waiting for dynamic content, animations, and network activity
- 🤖 **Interactions**: Programmable clicks, typing, scrolling, and other user interactions
- 🌓 **Dark Mode Support**: Capture web pages in dark mode with automatic detection
- 📍 **Geolocation Spoofing**: Simulate different geographic locations for localized testing

### Advanced Features

- 🚀 **Single Browser Context**: Efficient resource sharing and consistent performance through a shared browser context
- 🛡️ **Built-in Protection**: Automatic popup blocking and cookie consent handling (via optional extensions)
- 💾 **Response Caching**: Reduce load and improve response times with configurable caching (disabled by default)
- ⚖️ **Rate Limiting**: Prevent abuse and ensure fair usage with configurable request throttling
- 🔍 **Health Monitoring**: Built-in health checks and metrics for monitoring and alerts
- 🔄 **Error Recovery**: Automatic cleanup and retry mechanisms for robust operation
- 🔌 **Custom JavaScript Injection**: Execute custom scripts before capture for advanced manipulation

### Performance & Reliability

- ⚡ **Resource Optimization**: Efficient browser instance pooling and resource management
- 🏎️ **Fast Execution**: Optimized for speed with asynchronous operations and intelligent waiting strategies
- 📈 **Scalable Architecture**: Designed to handle high-concurrency scenarios and scale horizontally
- 📊 **Comprehensive Metrics**: Detailed performance metrics for monitoring and optimization
- 💪 **Robust Error Handling**: Graceful handling of network issues, timeouts, and unexpected errors

## 🚀 Quick Start

### Docker Deployment

```bash
# Pull and run the latest version
docker run -p 8080:8080 \
  -e AUTH_TOKEN=your_secret_token \
  -e USE_POPUP_BLOCKER=true \
  -e USE_COOKIE_BLOCKER=true \
  gpriday/pixashot:latest
```

### Basic Usage

```bash
curl -X POST http://localhost:8080/capture \
  -H "Authorization: Bearer your_secret_token" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "format": "png",
    "full_page": true,
    "wait_for_network": "idle",
    "window_width": 1920,
    "window_height": 1080
  }'
```

## 💡 Use Cases

- **Visual Regression Testing**: Automated UI validation and cross-browser testing
- **Content Archiving**: High-fidelity web page preservation for compliance and historical records
- **Thumbnail Generation**: Dynamic preview creation for websites, articles, and products
- **PDF Generation**: Convert web pages to professional, print-ready PDF documents
- **SEO Monitoring**: Track visual changes and verify meta content for search engine optimization
- **Social Media Cards**: Generate dynamic and visually appealing social media previews
- **Legal Compliance**: Capture and store web pages for legal evidence and regulatory requirements
- **Content Monitoring**: Monitor websites for visual changes, content updates, or defacement
- **Competitive Analysis**: Track competitors' websites and analyze their visual strategies
- **Brand Monitoring**: Ensure brand consistency across different platforms and devices

## 🛠️ Configuration

### Essential Environment Variables

```bash
# Required Settings
AUTH_TOKEN=your_secret_token # Secure API access
PORT=8080                    # Server port

# Worker Configuration
WORKERS=4                    # Number of worker processes (default: 4)
MAX_REQUESTS=1000            # Maximum requests per worker before restart (default: 1000)
KEEP_ALIVE=300               # Keep-alive timeout in seconds (default: 300)

# Feature Toggles
USE_POPUP_BLOCKER=true       # Enable/Disable popup blocking extension
USE_COOKIE_BLOCKER=true      # Enable/disable cookie consent handling extension
```

### Advanced Options

```bash
# Rate Limiting (defaults to disabled)
RATE_LIMIT_ENABLED=true      
RATE_LIMIT_CAPTURE="5 per second" # Rate limit for the capture endpoint
RATE_LIMIT_SIGNED="10 per second" # Rate limit for signed URLs

# Caching (defaults to disabled)
CACHE_MAX_SIZE=1000          # Maximum number of responses to cache

# Proxy Configuration (optional)
PROXY_SERVER=proxy.example.com
PROXY_PORT=8080
PROXY_USERNAME=user
PROXY_PASSWORD=pass
```

## 📚 Documentation

Complete documentation is available at [https://pixashot.com/docs](https://pixashot.com/docs), including:

- [Getting Started Guide](docs/getting-started/index.md)
- [Installation Guide](docs/getting-started/installation.md)
- [Configuration Guide](docs/getting-started/configuration.md)
- [API Reference](docs/api-reference/index.md)
- [Deployment Strategies](docs/deployment/index.md)
- [Security Best Practices](docs/security/best-practices.md)
- [Performance Optimization](docs/deployment/scaling.md)
- [Code Examples](docs/code-examples/index.md)
- [Troubleshooting Guide](docs/troubleshooting/index.md)
- [Use Cases](docs/use-cases/index.md)

## 🔒 Security Features

- **Authentication**: Token-based authentication using `Authorization: Bearer` header.
- **Signed URLs**: Securely generate time-limited, signed URLs for screenshot requests.
- **Rate Limiting**: Configurable request throttling to prevent abuse and ensure fair usage.
- **Input Validation**: Robust validation of all request parameters to prevent injection attacks.
- **Resource Control**: Configurable limits on memory, CPU, and network usage to prevent resource exhaustion.
- **HTTPS Support**: Secure communication with HTTPS termination (when used with a reverse proxy or load balancer).
- **Network Security**: Support for proxy servers and domain/IP restrictions.
- **Security Headers**: Automatic setting of recommended security headers in responses.
- **Regular Security Audits**: Ongoing security assessments and updates to address potential vulnerabilities.

## 🚀 Deployment Options

- **Docker**: Quick and easy deployment with our official Docker image.
- **Google Cloud Run**: Fully managed, serverless deployment on Google Cloud Platform (recommended for production).
- **Kubernetes**: Deploy and manage Pixashot on your Kubernetes cluster.
- **AWS ECS/Fargate**: Containerized deployment on Amazon Web Services.
- **Azure Container Instances**: Containerized deployment on Microsoft Azure.
- **Self-hosted**: Deploy on your own infrastructure for maximum control and customization.

## 💰 Cost Efficiency

- **Optimized Resource Usage**: Efficient use of CPU and memory, especially with the single browser context
  architecture.
- **Stateless Design**: Enables horizontal scaling and cost-effective use of cloud resources.
- **Google Cloud Run Free Tier**: Deploying on Google Cloud Run allows you to leverage their generous free tier:
    - 2 million requests/month
    - 360,000 vCPU-seconds
    - 180,000 GiB-seconds
    - Many users can operate within the free tier limits.

## 🤝 Support

- **Documentation**: [https://pixashot.com/docs](https://pixashot.com/docs)
- **Email Support**: [support@pixashot.com](mailto:support@pixashot.com)
- **Issue Tracking**: [GitHub Issues](https://github.com/pixashot/pixashot/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/pixashot/pixashot/discussions)

## 🌟 Getting Started

1. **Installation**

```bash
# Using Docker
docker pull gpriday/pixashot:latest

# Or on Google Cloud Run (replace with your desired configuration)
gcloud run deploy pixashot \
  --image gpriday/pixashot:latest \
  --platform managed \
  --allow-unauthenticated \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars="AUTH_TOKEN=your_secret_token"
```

2. **Configuration**

```bash
# Set required environment variables
export AUTH_TOKEN=$(openssl rand -hex 32)
export USE_POPUP_BLOCKER=true
export USE_COOKIE_BLOCKER=true
```

3. **Verification**

```bash
# Check health endpoint (replace with your service URL if deploying to Cloud Run)
curl http://localhost:8080/health

# Test capture endpoint
curl -X POST http://localhost:8080/capture \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","format":"png"}'
```

## 📝 License

Pixashot is open source software licensed under the MIT license. See the [LICENSE](LICENSE) file for more details.

## 🙏 Acknowledgements

Built with powerful open source technologies:

- [Quart](https://quart.palletsprojects.com/) - An asynchronous Python web microframework.
- [Playwright](https://playwright.dev/) - A browser automation library for reliable end-to-end testing and web scraping.
- [PopUpOFF](https://github.com/AdguardTeam/PopUpOFF) - A browser extension to block popups and overlays.
- [I don't care about cookies](https://www.i-dont-care-about-cookies.eu/) - A browser extension to get rid of cookie
  warnings.

Get started with Pixashot today and elevate your web capture capabilities! 🚀