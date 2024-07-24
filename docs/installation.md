# Installation

## Requirements

- Python 3.7+
- Flask
- Playwright
- Pillow
- Pydantic

For a complete list of dependencies, see `requirements.txt` in the project root.

## Steps

1. Clone the repository:
   ```
   git clone <repository-url>
   cd pixashot
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```
   playwright install
   ```

## Docker Installation

To build and run the service using Docker:

1. Build the Docker image:
   ```
   docker build -t pixashot .
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 pixashot
   ```

The service will be available at `http://localhost:8080`.

For deployment instructions, please refer to the [Deployment](deployment.md) guide.