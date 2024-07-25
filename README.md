# Pixashot: High-Quality Web Screenshot Service

Pixashot is a powerful, flexible, and easy-to-use web screenshot service. Built with Flask and Playwright, it offers a wide range of customization options to capture web pages exactly as you need them.

## 🌟 Features

- 📸 Capture full-page or viewport-specific screenshots
- 🖼️ Support for multiple image formats (PNG, JPEG, WebP)
- 📱 Custom viewport size configuration
- ⏱️ Wait for specific page elements before capture
- 🧰 Custom JavaScript injection for page manipulation
- 🚫 Built-in popup and cookie consent blockers
- 🔒 Proxy support for accessing restricted content
- 📜 Scroll-to-bottom functionality for dynamic content
- 🎨 Configurable image quality and pixel density
- 🐳 Docker support for easy deployment

[Learn more about Pixashot's features](docs/features.md) and check the [API examples](docs/api-examples.md).

## 🚀 Quickstart

Get Pixashot up and running in minutes:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pixashot.git
   cd pixashot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the server:
   ```
   python src/app.py
   ```

4. Capture your first screenshot:
   ```
   curl -X POST http://localhost:8080/capture \
        -H "Content-Type: application/json" \
        -d '{"url": "https://example.com", "format": "png"}'
   ```

For more detailed instructions, check out our [Installation Guide](docs/installation.md) and [Usage Guide](docs/usage.md).

## 📚 Documentation

- [API Reference](docs/api-reference.md)
- [Configuration Options](docs/configuration-options.md)
- [Advanced Features](docs/advanced-features.md)
- [Deployment Guide](docs/deployment.md)

## 🐳 Docker Support

Pixashot comes with built-in Docker support for easy deployment. [Learn more about Docker deployment](docs/deployment.md#docker-deployment)

## 🛠️ Use Cases

Pixashot is perfect for:

- Automated web testing and monitoring
- Creating website thumbnails
- Archiving web pages
- Generating social media preview images
- And much more!

## 🤝 Contributing

We welcome contributions! Check out our [Contributing Guide](docs/contributing.md) to get started.

## 📄 License

Pixashot is open source software licensed under the MIT license. See the [LICENSE](LICENSE) file for more details.

## 🌐 Community and Support

- [GitHub Issues](https://github.com/gregpriday/pixashot/issues) for bug reports and feature requests
- [GitHub Discussions](https://github.com/gregpriday/pixashot/discussions) for questions and community discussions
- Follow us on [Twitter](https://twitter.com/pixashot) for updates
- Read our [troubleshooting guide](docs/troubleshooting.md).

## Acknowledgements

- Pixashot is build using [Flask](https://flask.palletsprojects.com/en/3.0.x/) and [Playwright](https://playwright.dev/).
- We use [PopUpOFF](https://chromewebstore.google.com/detail/popupoff-popup-and-overla/ifnkdbpmgkdbfklnbfidaackdenlmhgh?hl=en) and [I don't care about cookies](https://chromewebstore.google.com/detail/i-dont-care-about-cookies/fihnjjcciajhdojfnbdddfaoknhalnja) to help create clean screenshots.