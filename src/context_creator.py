import os
import tempfile

class ContextCreator:
    def __init__(self):
        self.extension_dir = os.path.join(os.path.dirname(__file__), 'extensions')

    def create_context(self, playwright, options):
        temp_dir = tempfile.gettempdir()
        user_data_dir = os.path.join(temp_dir, 'chrome-user-data')

        extensions = self._get_extensions(options)
        context_options = self._create_context_options(options, user_data_dir, extensions)

        if options.block_media:
            context_options['route_handler'] = self._block_media

        return playwright.chromium.launch_persistent_context(**context_options)

    def _get_extensions(self, options):
        extensions = []
        if options.use_popup_blocker:
            # Load: https://chromewebstore.google.com/detail/popupoff-popup-and-overla/ifnkdbpmgkdbfklnbfidaackdenlmhgh?hl=en
            extensions.append(os.path.join(self.extension_dir, 'popup-off'))
        if options.use_cookie_blocker:
            # Load: https://chromewebstore.google.com/detail/i-dont-care-about-cookies/fihnjjcciajhdojfnbdddfaoknhalnja
            extensions.append(os.path.join(self.extension_dir, 'dont-care-cookies'))
        return extensions

    def _create_context_options(self, options, user_data_dir, extensions):
        context_options = {
            "user_data_dir": user_data_dir,
            "headless": True,
            "ignore_https_errors": options.ignore_https_errors,
            "device_scale_factor": options.pixel_density,
            "viewport": {
                "width": options.window_width,
                "height": options.window_height
            },
            "args": self._get_browser_args(extensions),
        }

        if options.proxy_server and options.proxy_port:
            context_options["proxy"] = {
                "server": f"{options.proxy_server}:{options.proxy_port}",
                "username": options.proxy_username,
                "password": options.proxy_password
            }

        return context_options

    def _get_browser_args(self, extensions):
        args = [
            '--autoplay-policy=no-user-gesture-required',
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            '--disable-accelerated-video-decode',
            '--disable-gpu-compositing',
            '--disable-gpu-rasterization',
            '--no-sandbox'
        ]

        if extensions:
            disable_extensions_arg = f"--disable-extensions-except={','.join(extensions)}"
            load_extension_args = [f"--load-extension={ext}" for ext in extensions]
            args.extend([disable_extensions_arg, *load_extension_args])

        return args

    def _block_media(self, route, request):
        if request.resource_type in ['image', 'media', 'font']:
            return route.abort()
        return route.continue_()