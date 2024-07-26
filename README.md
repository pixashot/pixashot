# 📸 Pixashot: Your Ultimate Web Screenshot Solution

Pixashot is a powerful, flexible, and developer-friendly web screenshot service that simplifies the process of capturing high-quality screenshots. Built with Flask and Playwright, Pixashot offers a wide range of customization options to capture web pages exactly as you need them.

## ✨ Why Choose Pixashot?

- 🎨 **Pixel-perfect quality**: Renders for any screen size, including Retina displays
- 🔧 **Highly customizable**: Supports dark mode, custom JavaScript injection, and more
- 🌐 **Full-page capture**: Takes screenshots of entire web pages, including lazy-loaded content
- 🛡️ **Built-in blockers**: Removes annoying popups, cookie banners, and ads
- 🔒 **Secure**: Supports proxy configuration and HTTPS error handling
- 💰 **Cost-effective**: [Deploy on Google Cloud Run](docs/deploy-from-dockerhub.md) - their free tier and capture over 20,000 screenshots per month at no cost!

## 🚀 Quick Start with Docker

Get Pixashot up and running in minutes using Docker:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pixashot.git
   cd pixashot
   ```

2. Build the Docker image:
   ```
   docker build -t pixashot .
   ```

3. Run the container:
   ```
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

That's it! Pixashot is now running in a Docker container, ready to capture screenshots. No need to worry about installing dependencies or setting up the environment manually.

## 📚 Documentation

- [API Reference](docs/api-reference.md): Detailed guide on Pixashot's API endpoints and usage
- [Configuration Options](docs/configuration.md): Comprehensive list of all available configuration parameters
- [Advanced Features](docs/advanced.md): Explore powerful capabilities like custom JavaScript injection and proxy configuration
- [Deployment Guide](docs/deployment.md): Step-by-step instructions for deploying Pixashot in various environments
- [Deploy on Google Cloud Run](docs/deploy-from-dockerhub.md): Specific guide for quick deployment on Google Cloud Run
- [Interactions](docs/interactions.md): Learn how to simulate user interactions before capturing screenshots

## 🌟 Features

- 📸 Capture full-page or viewport-specific screenshots
- 🖼️ Support for multiple output formats: PNG, JPEG, WebP, PDF, and HTML
- 📄 Capture from URLs or raw HTML input
- 🖨️ Generate high-quality PDFs with customizable options
- 🔄 Capture HTML output, perfect for scraping JavaScript-rendered pages
- 📱 Custom viewport size configuration
- ⏱️ Wait for specific page elements before capture
- 🧰 Custom JavaScript injection for page manipulation
- 🚫 Built-in popup and cookie consent blockers
- 🔒 Proxy support for accessing restricted content
- 🎨 Configurable image quality and pixel density
- 🌓 Dark mode support for captures
- 📍 Geolocation spoofing capabilities
- 🐳 Docker support for easy deployment and scalability

[Learn more about Pixashot's features](docs/features.md) and check out our [API examples](docs/api-examples.md).

## 💻 Use Cases

Pixashot is perfect for:

- 🧪 Automated web testing and monitoring
- 🖼️ Creating website thumbnails
- 📚 Archiving web pages
- 🐦 Generating social media preview images
- 🔍 SEO analysis and reporting
- And much more!

## 🤝 Contributing

We welcome contributions! Check out our [Contributing Guide](docs/contributing.md) to get started.

## 📄 License

Pixashot is open source software licensed under the MIT license. See the [LICENSE](LICENSE) file for more details.

## 🌐 Community and Support

- [GitHub Issues](https://github.com/yourusername/pixashot/issues) for bug reports and feature requests
- [GitHub Discussions](https://github.com/yourusername/pixashot/discussions) for questions and community discussions
- Read our [troubleshooting guide](docs/troubleshooting.md) for quick solutions to common issues

## 🙏 Acknowledgements

- Pixashot is built using [Flask](https://flask.palletsprojects.com/en/3.0.x/) and [Playwright](https://playwright.dev/).
- We use [PopUpOFF](https://chromewebstore.google.com/detail/popupoff-popup-and-overla/ifnkdbpmgkdbfklnbfidaackdenlmhgh?hl=en) and [I don't care about cookies](https://chromewebstore.google.com/detail/i-dont-care-about-cookies/fihnjjcciajhdojfnbdddfaoknhalnja) to help create clean screenshots.

Start capturing stunning screenshots with Pixashot today! 🚀📸