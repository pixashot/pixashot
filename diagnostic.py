#!/usr/bin/env python3
import asyncio
import logging
import sys
import time
import psutil
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class UrlDiagnostics:
    def __init__(self):
        self.metrics = {
            'timing': {},
            'memory': {},
            'network': {
                'requests': [],
                'failed_requests': [],
                'status_codes': {}
            },
            'page': {
                'errors': [],
                'console_messages': [],
                'headers': {},
                'html': None
            },
            'resources': {
                'total_size': 0,
                'by_type': {}
            }
        }

    async def run_diagnostics(self, url):
        start_time = time.time()
        self.metrics['timing']['start'] = datetime.now().isoformat()

        try:
            async with async_playwright() as playwright:
                # Launch browser with detailed logging
                browser = await playwright.chromium.launch(
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        '--hide-scrollbars',
                        '--mute-audio'
                    ]
                )

                # Create context and page
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    device_scale_factor=1.0
                )
                page = await context.new_page()

                # Record memory before navigation
                self.record_memory('before_navigation')

                # Set up event listeners
                await self._setup_page_listeners(page)

                try:
                    # Navigate to the URL with a generous timeout
                    logger.info(f"Navigating to {url}")
                    response = await page.goto(url, timeout=30000, wait_until='networkidle')

                    if response:
                        self.metrics['page']['status'] = response.status
                        self.metrics['page']['status_text'] = response.status_text
                        self.metrics['page']['headers'] = dict(response.headers)

                    # Record memory after navigation
                    self.record_memory('after_navigation')

                    # Gather page metrics
                    await self._gather_page_metrics(page)

                    # Take a screenshot
                    screenshot_path = f"diagnostic_screenshot_{int(time.time())}.png"
                    await page.screenshot(path=screenshot_path)
                    logger.info(f"Screenshot saved to {screenshot_path}")

                except Exception as e:
                    logger.error(f"Error during page navigation: {str(e)}")
                    self.metrics['error'] = str(e)

                finally:
                    # Record final memory state
                    self.record_memory('final')

                    # Close browser
                    await browser.close()

        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
            self.metrics['fatal_error'] = str(e)

        # Record timing
        self.metrics['timing']['end'] = datetime.now().isoformat()
        self.metrics['timing']['total_seconds'] = time.time() - start_time

        # Save metrics to file
        self._save_metrics()

    def record_memory(self, checkpoint):
        """Record memory usage at a specific checkpoint."""
        process = psutil.Process()
        self.metrics['memory'][checkpoint] = {
            'rss_mb': process.memory_info().rss / (1024 * 1024),
            'vms_mb': process.memory_info().vms / (1024 * 1024),
            'percent': process.memory_percent(),
            'num_threads': process.num_threads(),
            'cpu_percent': process.cpu_percent()
        }

    async def _setup_page_listeners(self, page):
        """Set up page event listeners with proper failure handling."""
        page.on('console', lambda msg: self.metrics['page']['console_messages'].append(
            {'type': msg.type, 'text': msg.text}
        ))

        page.on('pageerror', lambda err: self.metrics['page']['errors'].append(str(err)))

        page.on('request', lambda request: self.metrics['network']['requests'].append({
            'url': request.url,
            'method': request.method,
            'resource_type': request.resource_type,
            'time': time.time()
        }))

        # Fixed failure handling
        page.on('requestfailed', lambda request: self.metrics['network']['failed_requests'].append({
            'url': request.url,
            'method': request.method,
            'failure': str(request.failure) if request.failure else 'Unknown error',
            'time': time.time()
        }))

        page.on('response', lambda response: self._handle_response(response))

    def _handle_response(self, response):
        """Handle response metrics."""
        status = response.status
        if status not in self.metrics['network']['status_codes']:
            self.metrics['network']['status_codes'][status] = 0
        self.metrics['network']['status_codes'][status] += 1

    async def _gather_page_metrics(self, page):
        """Gather detailed page metrics."""
        # Get page content
        self.metrics['page']['html'] = await page.content()

        # Get performance metrics
        performance_metrics = await page.evaluate("""() => {
            const nav = performance.getEntriesByType('navigation')[0];
            const resources = performance.getEntriesByType('resource');

            return {
                navigation: nav ? {
                    domComplete: nav.domComplete,
                    loadEventEnd: nav.loadEventEnd,
                    domInteractive: nav.domInteractive,
                    domContentLoaded: nav.domContentLoadedEventEnd
                } : null,
                resources: resources.map(r => ({
                    name: r.name,
                    type: r.initiatorType,
                    duration: r.duration,
                    size: r.transferSize || 0
                }))
            };
        }""")

        self.metrics['performance'] = performance_metrics

        # Calculate resource metrics
        for resource in performance_metrics.get('resources', []):
            resource_type = resource.get('type', 'other')
            if resource_type not in self.metrics['resources']['by_type']:
                self.metrics['resources']['by_type'][resource_type] = {
                    'count': 0,
                    'total_size': 0,
                    'total_duration': 0
                }

            self.metrics['resources']['by_type'][resource_type]['count'] += 1
            self.metrics['resources']['by_type'][resource_type]['total_size'] += resource.get('size', 0)
            self.metrics['resources']['by_type'][resource_type]['total_duration'] += resource.get('duration', 0)
            self.metrics['resources']['total_size'] += resource.get('size', 0)

        # Get page metrics
        metrics = await page.evaluate("""() => ({
            documentHeight: document.documentElement.scrollHeight,
            documentWidth: document.documentElement.scrollWidth,
            scripts: document.scripts.length,
            images: document.images.length,
            forms: document.forms.length,
            links: document.links.length,
            domElements: document.getElementsByTagName('*').length
        })""")

        self.metrics['page']['metrics'] = metrics

    def _save_metrics(self):
        """Save metrics to a file."""
        timestamp = int(time.time())
        metrics_file = f'url_diagnostics_{timestamp}.json'
        html_file = f'url_diagnostics_{timestamp}.html'

        # Save full metrics including HTML
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2)

        # Save HTML separately for easier viewing
        if self.metrics['page'].get('html'):
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(self.metrics['page']['html'])

        logger.info(f"Metrics saved to {metrics_file}")
        logger.info(f"HTML saved to {html_file}")

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print a summary of the diagnostics."""
        print("\n=== Diagnostics Summary ===")
        print(f"Duration: {self.metrics['timing']['total_seconds']:.2f} seconds")
        print("\nMemory Usage (MB):")
        for checkpoint, data in self.metrics['memory'].items():
            print(f"  {checkpoint}: {data['rss_mb']:.1f} MB RSS")

        print("\nNetwork:")
        print(f"  Total Requests: {len(self.metrics['network']['requests'])}")
        print(f"  Failed Requests: {len(self.metrics['network']['failed_requests'])}")
        print("  Status Codes:", dict(self.metrics['network']['status_codes']))

        print("\nPage Metrics:")
        if 'metrics' in self.metrics['page']:
            metrics = self.metrics['page']['metrics']
            print(f"  DOM Elements: {metrics['domElements']}")
            print(f"  Scripts: {metrics['scripts']}")
            print(f"  Images: {metrics['images']}")
            print(f"  Document Size: {metrics['documentWidth']}x{metrics['documentHeight']}")

        print("\nErrors:", len(self.metrics['page']['errors']))
        if self.metrics['page']['errors']:
            for error in self.metrics['page']['errors']:
                print(f"  - {error}")


async def main():
    if len(sys.argv) != 2:
        print("Usage: python diagnostic.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    diagnostics = UrlDiagnostics()
    await diagnostics.run_diagnostics(url)


if __name__ == "__main__":
    asyncio.run(main())