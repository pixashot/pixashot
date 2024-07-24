import logging
from typing import Dict
from playwright.sync_api import Page
from exceptions import BrowserException
from controllers.base_controller import BaseBrowserController

logger = logging.getLogger(__name__)

class GeolocationController(BaseBrowserController):
    def __init__(self):
        super().__init__()

    def set_geolocation(self, page: Page, location: Dict[str, float]):
        try:
            context = page.context
            context.grant_permissions(['geolocation'])
            context.set_geolocation(location)

            page.add_init_script("""
                const mockGeolocation = {
                    getCurrentPosition: (success) => {
                        success({
                            coords: {
                                latitude: %f,
                                longitude: %f,
                                accuracy: %f,
                                altitude: null,
                                altitudeAccuracy: null,
                                heading: null,
                                speed: null
                            },
                            timestamp: Date.now()
                        });
                    },
                    watchPosition: (success) => {
                        success({
                            coords: {
                                latitude: %f,
                                longitude: %f,
                                accuracy: %f,
                                altitude: null,
                                altitudeAccuracy: null,
                                heading: null,
                                speed: null
                            },
                            timestamp: Date.now()
                        });
                        return 0;
                    },
                };
                Object.defineProperty(navigator, 'geolocation', {
                    value: mockGeolocation,
                    configurable: true,
                });
            """ % (location['latitude'], location['longitude'], location['accuracy'],
                   location['latitude'], location['longitude'], location['accuracy']))

            logger.info(f"Geolocation set to: {location}")
        except Exception as e:
            logger.error(f"Error setting geolocation: {str(e)}")
            raise BrowserException(f"Failed to set geolocation: {str(e)}")