import logging
from playwright.sync_api import Page
from exceptions import InteractionException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class InteractionController(BaseBrowserController):
    def perform_interactions(self, page: Page, interactions: list):
        for step in interactions:
            try:
                if step.action == "click":
                    self._click(page, step.selector)
                elif step.action == "type":
                    self._type(page, step.selector, step.text)
                elif step.action == "wait":
                    self._wait(page, step.duration)
                elif step.action == "hover":
                    self._hover(page, step.selector)
                elif step.action == "scroll":
                    self._scroll(page, step.x, step.y)
            except Exception as e:
                logger.error(f"Error performing interaction {step.action}: {str(e)}")
                raise InteractionException(f"Failed to perform {step.action}: {str(e)}")

    def _click(self, page: Page, selector: str):
        page.click(selector)

    def _type(self, page: Page, selector: str, text: str):
        page.fill(selector, text)

    def _wait(self, page: Page, duration: int):
        page.wait_for_timeout(duration)

    def _hover(self, page: Page, selector: str):
        page.hover(selector)

    def _scroll(self, page: Page, x: int, y: int):
        page.evaluate(f"window.scrollTo({x}, {y})")

    def wait_for_animations(self, page: Page, timeout: int = 5000):
        try:
            page.evaluate(f"""
                () => new Promise((resolve) => {{
                    const checkAnimations = () => {{
                        const animating = document.querySelector(':scope *:not(:where(:hover, :active))');
                        if (!animating) {{
                            resolve();
                        }} else {{
                            requestAnimationFrame(checkAnimations);
                        }}
                    }};
                    checkAnimations();
                    setTimeout(resolve, {timeout});
                }})
            """)
        except Exception as e:
            logger.warning(f"Error waiting for animations: {str(e)}")
