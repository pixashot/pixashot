import logging
from typing import Dict, Optional
from playwright.sync_api import Page
from exceptions import BrowserException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)


class GeolocationController(BaseBrowserController):
    def set_geolocation(self, page: Page, location: Optional[Dict[str, float]]):
        if location is None:
            logger.info("No geolocation set, skipping geolocation configuration")
            return

        try:
            context = page.context
            context.grant_permissions(['geolocation'])
            context.set_geolocation(location)

            # Handle both dictionary and mock object
            latitude = location['latitude'] if isinstance(location, dict) else location.latitude
            longitude = location['longitude'] if isinstance(location, dict) else location.longitude
            accuracy = location['accuracy'] if isinstance(location, dict) else location.accuracy

            page.add_init_script(f"""
                const mockGeolocation = {{
                    getCurrentPosition: (success) => {{
                        success({{
                            coords: {{
                                latitude: {latitude},
                                longitude: {longitude},
                                accuracy: {accuracy},
                                altitude: null,
                                altitudeAccuracy: null,
                                heading: null,
                                speed: null
                            }},
                            timestamp: Date.now()
                        }});
                    }},
                    watchPosition: (success) => {{
                        success({{
                            coords: {{
                                latitude: {latitude},
                                longitude: {longitude},
                                accuracy: {accuracy},
                                altitude: null,
                                altitudeAccuracy: null,
                                heading: null,
                                speed: null
                            }},
                            timestamp: Date.now()
                        }});
                        return 0;
                    }},
                }};
                Object.defineProperty(navigator, 'geolocation', {{
                    value: mockGeolocation,
                    configurable: true,
                }});
            """)

            logger.info(f"Geolocation set to: {location}")
        except Exception as e:
            logger.error(f"Error setting geolocation: {str(e)}")
            raise BrowserException(f"Failed to set geolocation: {str(e)}")
