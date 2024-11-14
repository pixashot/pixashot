# 📸 Pixashot: High-Performance Web Screenshot Service

Pixashot is a reliable, production-ready web screenshot service that captures pixel-perfect screenshots with extensive customization options. Built with modern browser automation and designed for stability, it's suitable for automated testing, content archival, and various production use cases.

**Note**: Pixashot is actively developed and continuously improving. Check our [public roadmap](ROADMAP.md) for upcoming features and enhancements.

## ✨ Key Features

### Core Capabilities
- 🎯 **Pixel-Perfect Capture**: High-fidelity screenshots at any resolution, including Retina displays
- 🌐 **Full Page Support**: Intelligent capture of scrollable content with dynamic height detection
- 📱 **Device Simulation**: Accurate mobile viewport emulation with customizable settings
- 🎨 **Multiple Formats**: PNG, JPEG, WebP, PDF, and HTML output options
- 🔄 **Dynamic Content**: Smart waiting for dynamic content, animations, and network activity

### Advanced Features
- 🚀 **Single Browser Context**: Efficient resource sharing and consistent performance
- 🛡️ **Built-in Protection**: Automatic popup and cookie consent handling
- 🌓 **Dark Mode Support**: Accurate dark mode simulation and capture
- 📍 **Geolocation Spoofing**: Precise location simulation for testing
- 🤖 **Interaction Simulation**: Programmable clicks, typing, and navigation sequences
- 🔒 **Security**: Token-based authentication and access control

### Performance & Reliability
- ⚡ **Resource Optimization**: Smart browser instance pooling
- 💾 **Response Caching**: Optional caching for repeated captures
- ⚖️ **Rate Limiting**: Configurable request throttling
- 🔍 **Health Monitoring**: Basic status checks and metrics
- 🔄 **Error Recovery**: Automatic cleanup of failed captures

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

- **Visual Testing**: Automated UI validation and regression testing
- **Content Archiving**: High-fidelity web page preservation
- **Thumbnail Generation**: Dynamic preview creation for web content
- **PDF Generation**: Convert web pages to professional PDF documents
- **SEO Monitoring**: Track visual changes and verify meta content
- **Social Media Cards**: Generate dynamic social media previews
- **Legal Compliance**: Document preservation and verification
- **Content Moderation**: Visual content review automation

## 🛠️ Configuration

### Essential Environment Variables
```bash
# Required Settings
AUTH_TOKEN=your_secret_token
PORT=8080

# Worker Configuration
WORKERS=4
MAX_REQUESTS=1000
KEEP_ALIVE=300

# Feature Toggles
USE_POPUP_BLOCKER=true
USE_COOKIE_BLOCKER=true

# Performance Options
RATE_LIMIT_ENABLED=false
CACHE_MAX_SIZE=1000
```

### Advanced Options
```bash
# Rate Limiting
RATE_LIMIT_CAPTURE="1 per second"
RATE_LIMIT_SIGNED="5 per second"

# Proxy Configuration
PROXY_SERVER=proxy.example.com
PROXY_PORT=8080
PROXY_USERNAME=user
PROXY_PASSWORD=pass
```

## 📚 Documentation

Complete documentation is available at [https://pixashot.com/docs](https://pixashot.com/docs), including:

- API Reference Guide
- Deployment Strategies
- Security Best Practices
- Performance Optimization
- Integration Examples
- Troubleshooting Guide

## 🔒 Security Features

- **Authentication**: Token-based auth and signed URLs
- **Rate Limiting**: Configurable request throttling
- **Input Validation**: Comprehensive request validation
- **Resource Control**: Memory and CPU limits
- **Network Security**: Proxy support and HTTPS handling
- **Access Control**: Fine-grained permission management

## 🚀 Deployment Options

- **Docker**: Quick deployment with our official image
- **Google Cloud Run**: Serverless deployment (recommended)
- **Kubernetes**: Enterprise-grade orchestration
- **AWS/Azure**: Major cloud platform support
- **Self-hosted**: Full control and customization

## 💰 Cost Efficiency

Deploy on Google Cloud Run to leverage the free tier:
- 2 million requests/month included
- 360,000 vCPU-seconds
- 180,000 GiB-seconds
- Most users stay within free tier limits

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

# Or on Google Cloud Run
gcloud run deploy pixashot \
  --image gpriday/pixashot:latest \
  --platform managed \
  --allow-unauthenticated
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
# Check health endpoint
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
- [Quart](https://quart.palletsprojects.com/) for async web framework
- [Playwright](https://playwright.dev/) for reliable browser automation
- [PopUpOFF](https://github.com/AdguardTeam/PopUpOFF) for popup blocking
- [I don't care about cookies](https://www.i-dont-care-about-cookies.eu/) for cookie notice handling

Get started with Pixashot today and elevate your web capture capabilities! 🚀