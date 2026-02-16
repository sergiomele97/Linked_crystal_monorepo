import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path. Unit tests are in app/tests/unit/, so src is ../../src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock External Dependencies
sys.modules['websockets'] = MagicMock()
sys.modules['asyncio'] = MagicMock()
sys.modules['threading'] = MagicMock()

# Mock Kivy Dependencies BEFORE importing connection_manager
sys.modules['kivy'] = MagicMock()
sys.modules['kivy.app'] = MagicMock()
sys.modules['kivy.core.window'] = MagicMock()
sys.modules['kivy.network.urlrequest'] = MagicMock()
sys.modules['kivy.uix.popup'] = MagicMock()
sys.modules['kivy.uix.button'] = MagicMock()
sys.modules['kivy.uix.scrollview'] = MagicMock()
sys.modules['kivy.uix.gridlayout'] = MagicMock()
sys.modules['kivy.metrics'] = MagicMock()
sys.modules['kivy.clock'] = MagicMock()
sys.modules['kivy.uix.label'] = MagicMock()

# Mock env
sys.modules['env'] = MagicMock()
sys.modules['env'].URL = "http://mock-url"

# Now we can import the module to test
from services.connection.main_conn.connection_manager import ConnectionManager

class TestVersionCheck(unittest.TestCase):
    def setUp(self):
        # Mock connection loop to avoid threads
        with patch('services.connection.main_conn.connection_manager.ConnectionLoop'):
            self.manager = ConnectionManager()
        
        self.manager._show_update_popup = MagicMock()
        self.manager._fetch_servers = MagicMock()
        
        # Mock parent screen
        self.parent_screen = MagicMock()
        self.parent_screen.ids.label_servidor.text = ""
        self.parent_screen.loading = False

    def test_version_ok(self):
        # Mock UrlRequest to simulate success response (same version)
        with patch('services.connection.main_conn.connection_manager.UrlRequest') as MockRequest:
            # Trigger logic
            self.manager.getServerListAndSelect(self.parent_screen)
            
            # UrlRequest is called with kwargs. Extract success callback
            # call_args is (args, kwargs)
            _, kwargs = MockRequest.call_args
            on_success = kwargs.get('on_success')
            
            # Simulate response: Server 0.1, Client 0.1
            with patch('version.__version__', "0.1"):
                on_success(None, {"version": "0.1"})
            
            # Should fetch servers
            self.manager._fetch_servers.assert_called_once()
            self.manager._show_update_popup.assert_not_called()

    def test_version_older_client(self):
        with patch('services.connection.main_conn.connection_manager.UrlRequest') as MockRequest:
            self.manager.getServerListAndSelect(self.parent_screen)
            _, kwargs = MockRequest.call_args
            on_success = kwargs.get('on_success')
            
            # Simulate response: Server 0.2, Client 0.1
            with patch('version.__version__', "0.1"):
                on_success(None, {"version": "0.2"})
            
            # Should BLOCK
            self.manager._show_update_popup.assert_called_once()
            self.manager._fetch_servers.assert_not_called()

    def test_version_newer_client(self):
        with patch('services.connection.main_conn.connection_manager.UrlRequest') as MockRequest:
            self.manager.getServerListAndSelect(self.parent_screen)
            _, kwargs = MockRequest.call_args
            on_success = kwargs.get('on_success')
            
            # Simulate response: Server 0.1, Client 0.2
            with patch('version.__version__', "0.2"):
                on_success(None, {"version": "0.1"})
            
            # Should ALLOW (forward compatibility)
            self.manager._fetch_servers.assert_called_once()
            self.manager._show_update_popup.assert_not_called()

if __name__ == '__main__':
    unittest.main()
