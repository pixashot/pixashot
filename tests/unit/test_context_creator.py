import pytest
from unittest.mock import Mock, patch
from src.context_manager import ContextManager
from src.capture_request import CaptureRequest


@pytest.fixture
async def context_manager():
    manager = ContextManager()
    await manager.initialize(Mock())
    return manager


@pytest.fixture
def mock_options():
    return CaptureRequest(
        url="https://example.com",
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


def test_get_extensions(context_manager, mock_options):
    extensions = context_manager._get_extensions(mock_options)
    assert len(extensions) == 2
    assert any('popup-off' in ext for ext in extensions)
    assert any('dont-care-cookies' in ext for ext in extensions)


def test_get_browser_args(context_manager):
    extensions = ['/path/to/extension1', '/path/to/extension2']
    args = context_manager._get_browser_args(extensions)
    assert '--disable-extensions-except=/path/to/extension1,/path/to/extension2' in args
    assert '--load-extension=/path/to/extension1' in args
    assert '--load-extension=/path/to/extension2' in args


@pytest.mark.asyncio
async def test_get_context(context_manager, mock_options):
    mock_browser = Mock()
    mock_context = Mock()
    mock_browser.new_context.return_value = mock_context

    with patch.object(context_manager.playwright.chromium, 'launch', return_value=mock_browser):
        context = await context_manager.get_context(mock_options)

    assert context == mock_context
    mock_browser.new_context.assert_called_once()


@pytest.mark.asyncio
async def test_get_context_with_proxy(context_manager, mock_options):
    mock_options.proxy_server = 'proxy.example.com'
    mock_options.proxy_port = 8080
    mock_options.proxy_username = 'user'
    mock_options.proxy_password = 'pass'

    mock_browser = Mock()
    mock_context = Mock()
    mock_browser.new_context.return_value = mock_context

    with patch.object(context_manager.playwright.chromium, 'launch', return_value=mock_browser):
        context = await context_manager.get_context(mock_options)

    assert context == mock_context
    mock_browser.new_context.assert_called_once()
    call_args = mock_browser.new_context.call_args[1]
    assert call_args['proxy'] == {
        'server': 'proxy.example.com:8080',
        'username': 'user',
        'password': 'pass'
    }


@pytest.mark.asyncio
async def test_context_reuse(context_manager, mock_options):
    mock_browser = Mock()
    mock_context1 = Mock()
    mock_context2 = Mock()
    mock_browser.new_context.side_effect = [mock_context1, mock_context2]

    with patch.object(context_manager.playwright.chromium, 'launch', return_value=mock_browser):
        context1 = await context_manager.get_context(mock_options)
        context2 = await context_manager.get_context(mock_options)

    assert context1 == context2 == mock_context1
    assert mock_browser.new_context.call_count == 1


@pytest.mark.asyncio
async def test_context_max_limit(context_manager, mock_options):
    context_manager.max_contexts = 2
    mock_browser = Mock()
    mock_contexts = [Mock() for _ in range(3)]
    mock_browser.new_context.side_effect = mock_contexts

    with patch.object(context_manager.playwright.chromium, 'launch', return_value=mock_browser):
        contexts = [await context_manager.get_context(mock_options) for _ in range(3)]

    assert len(context_manager.contexts) == 2
    assert contexts[2] not in context_manager.contexts.values()
    assert mock_contexts[0].close.called