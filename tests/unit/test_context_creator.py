import pytest
from unittest.mock import Mock, patch
from src.context_creator import ContextCreator


@pytest.fixture
def context_creator():
    return ContextCreator()


@pytest.fixture
def mock_playwright():
    return Mock()


@pytest.fixture
def mock_options():
    return Mock(
        use_popup_blocker=True,
        use_cookie_blocker=True,
        ignore_https_errors=True,
        pixel_density=2.0,
        window_width=1280,
        window_height=720,
        proxy_server=None,
        proxy_port=None,
        block_media=False
    )


def test_get_extensions(context_creator, mock_options):
    extensions = context_creator._get_extensions(mock_options)
    assert len(extensions) == 2
    assert any('popup-off' in ext for ext in extensions)
    assert any('dont-care-cookies' in ext for ext in extensions)


def test_create_context_options(context_creator, mock_options):
    options = context_creator._create_context_options(mock_options, '/tmp/user_data', [])
    assert options['headless'] == True
    assert options['ignore_https_errors'] == True
    assert options['device_scale_factor'] == 2.0
    assert options['viewport'] == {'width': 1280, 'height': 720}


def test_create_context_options_with_proxy(context_creator, mock_options):
    mock_options.proxy_server = 'proxy.example.com'
    mock_options.proxy_port = 8080
    mock_options.proxy_username = 'user'
    mock_options.proxy_password = 'pass'

    options = context_creator._create_context_options(mock_options, '/tmp/user_data', [])
    assert options['proxy'] == {
        'server': 'proxy.example.com:8080',
        'username': 'user',
        'password': 'pass'
    }


@patch('tempfile.gettempdir', return_value='/tmp')
def test_create_context(mock_tempfile, context_creator, mock_playwright, mock_options):
    context = context_creator.create_context(mock_playwright, mock_options)
    mock_playwright.chromium.launch_persistent_context.assert_called_once()
    args = mock_playwright.chromium.launch_persistent_context.call_args[1]
    assert '/tmp/chrome-user-data' in args['user_data_dir']
    assert args['headless'] == True
    assert args['ignore_https_errors'] == True


def test_block_media(context_creator):
    mock_route = Mock()
    mock_request = Mock(resource_type='image')

    context_creator._block_media(mock_route, mock_request)
    mock_route.abort.assert_called_once()

    mock_request.resource_type = 'document'
    context_creator._block_media(mock_route, mock_request)
    mock_route.continue_.assert_called_once()