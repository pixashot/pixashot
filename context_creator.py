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

        return playwright.chromium.launch_persistent_context(**context_options)

    def _get_extensions(self, options):
        extensions = []
        if options.get('use_popup_blocker', True):
            extensions.append(os.path.join(self.extension_dir, 'popup-off'))
        if options.get('use_cookie_blocker', True):
            extensions.append(os.path.join(self.extension_dir, 'dont-care-cookies'))
        return extensions

    def _create_context_options(self, options, user_data_dir, extensions):
        context_options = {
            "user_data_dir": user_data_dir,
            "headless": options.get('headless', False),
            "ignore_https_errors": options.get('ignore_https_errors', True),
            "device_scale_factor": options.get('pixel_density', 2.0),
            "viewport": {
                "width": options.get('windowWidth', 1280),
                "height": options.get('windowHeight', 720)
            },
            "args": self._get_browser_args(extensions),
        }

        if options.get('proxy_server') and options.get('proxy_port'):
            context_options["proxy"] = {
                "server": f"{options['proxy_server']}:{options['proxy_port']}",
                "username": options.get('proxy_username'),
                "password": options.get('proxy_password')
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
