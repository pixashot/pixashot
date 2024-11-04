# 📸 Pixashot: Your Ultimate Web Screenshot Solution

Pixashot is a powerful, flexible, and developer-friendly web screenshot service that simplifies the process of capturing high-quality screenshots. Built with Quart and Playwright, Pixashot offers a comprehensive suite of customization options to capture web pages exactly as you need them.

## ✨ Why Choose Pixashot?

Firstly, please take a look at our [public development roadmap](ROADMAP.md) to get an idea of where Pixashot is heading.

- 🎨 **Pixel-perfect quality**: High-resolution captures with configurable DPR for retina displays
- 🔧 **Highly customizable**: Supports dark mode, custom JavaScript injection, user agent spoofing, and more
- 🌐 **Full-page capture**: Takes screenshots of entire web pages, including dynamically loaded content
- 🛡️ **Built-in blockers**: Removes annoying popups, cookie banners, and unwanted media content
- 🔒 **Enterprise-ready**: Supports authentication, rate limiting, proxy configuration, and HTTPS error handling
- 💰 **Cost-effective**: [Deploy on Google Cloud Run](docs/deploy-from-dockerhub.md) using their free tier and capture over 20,000 screenshots per month at no cost!

## 🚀 Quick Start with Docker

Get Pixashot up and running in minutes using Docker:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pixashot.git
   cd pixashot
   ```

2. Build the Docker image:
   ```bash
   docker build -t pixashot .
   ```

3. Run the container:
   ```bash
   docker run -p 8080:8080 pixashot
   ```

4. Capture your first screenshot:
   ```bash
   curl -X POST http://localhost:8080/capture \
        -H "Content-Type: application/json" \
        -d '{
              "url": "https://example.com",
              "format": "png",
              "full_page": true,
              "window_width": 1920,
              "window_height": 1080
            }'
   ```

That's it! Pixashot is now running in a Docker container, ready to capture screenshots. The container includes all necessary dependencies, including a pre-configured browser environment.

## 📚 Documentation

- [API Reference](docs/api-reference.md): Complete guide to Pixashot's API endpoints and request/response formats
- [Configuration Options](docs/configuration.md): Comprehensive list of all available configuration parameters
- [Authentication](docs/authentication.md): Guide to token-based auth and signed URLs for secure access
- [Advanced Features](docs/advanced.md): Explore capabilities like JavaScript injection, proxy configuration, and more
- [Deployment Guide](docs/deployment.md): Step-by-step instructions for deploying Pixashot in various environments
- [Deploy on Google Cloud Run](docs/deploy-from-dockerhub.md): Quick deployment guide for Google Cloud Run
- [Interactions](docs/interactions.md): Simulate user interactions before capturing screenshots
- [Troubleshooting](docs/troubleshooting.md): Solutions for common issues and debugging tips

## 🌟 Key Features

### Capture Options
- 📸 Full-page or viewport-specific screenshots
- 🖼️ Multiple output formats: PNG, JPEG, WebP, PDF, and HTML
- 📄 Capture from URLs or raw HTML content
- 📱 Configurable viewport sizes and pixel density
- 🎨 Adjustable image quality and transparency support
- 🌓 Dark mode support for captures

### Advanced Capabilities
- ⏱️ Flexible wait conditions (network, selectors, animations)
- 🧰 Custom JavaScript injection for page manipulation
- 🎭 User agent spoofing and header customization
- 🚫 Built-in popup and cookie consent blockers
- 📍 Geolocation spoofing
- 🔒 Proxy support with authentication
- 🖨️ Comprehensive PDF options (format, scaling, backgrounds)
- 🤖 Programmable interaction sequences

### Enterprise Features
- 🔑 Token-based authentication and signed URLs
- ⚡ Rate limiting and request throttling
- 💾 Optional response caching
- 🔍 Detailed error reporting
- 📊 Health check endpoints
- 🐳 Docker and Cloud Run support

[Learn more about Pixashot's features](docs/features.md) and check out our [API examples](docs/api-examples.md).

## 💻 Use Cases

Pixashot is perfect for:

- 🧪 Automated web testing and monitoring
- 🖼️ Creating website thumbnails and previews
- 📚 Web page archiving and preservation
- 🐦 Generating social media cards and previews
- 🔍 SEO analysis and reporting
- 📊 Automated report generation
- 🔄 Content moderation and verification
- And much more!

## 🛠️ Technical Stack

- **Framework**: Quart (async Flask-like framework)
- **Browser Automation**: Playwright
- **Container**: Docker with multi-stage builds
- **Testing**: pytest with async support
- **API Documentation**: OpenAPI/Swagger
- **Type Checking**: Pydantic for request validation
- **Monitoring**: Built-in health check endpoints

## 🤝 Contributing

We welcome contributions! Check out our [Contributing Guide](docs/contributing.md) to get started. We appreciate:

- 🐛 Bug reports and fixes
- ✨ New features and improvements
- 📚 Documentation updates
- 🧪 Test coverage improvements
- 💡 Feature suggestions

## 📄 License

Pixashot is open source software licensed under the MIT license. See the [LICENSE](LICENSE) file for more details.

## 🌐 Community and Support

- [GitHub Issues](https://github.com/yourusername/pixashot/issues) for bug reports and feature requests
- [GitHub Discussions](https://github.com/yourusername/pixashot/discussions) for questions and community discussions
- Join our community channels (coming soon!)

## 🙏 Acknowledgements

- Built on [Quart](https://quart.palletsprojects.com/) for high-performance async operations
- Powered by [Playwright](https://playwright.dev/) for reliable browser automation
- Uses [PopUpOFF](https://chromewebstore.google.com/detail/popupoff-popup-and-overla/ifnkdbpmgkdbfklnbfidaackdenlmhgh) for popup blocking
- Integrates [I don't care about cookies](https://chromewebstore.google.com/detail/i-dont-care-about-cookies/fihnjjcciajhdojfnbdddfaoknhalnja) for cookie notice handling

Start capturing stunning screenshots with Pixashot today! 🚀📸