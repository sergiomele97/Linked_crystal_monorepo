import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Configure Kivy for headless testing if needed
os.environ['KIVY_NO_CONSOLELOG'] = '1'

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import kivy.lang
# Patch Builder.load_file globally for components that might load KV during import
# Also patch App.get_running_app to avoid issues with ConnectionLoop initialization
with patch('kivy.lang.Builder.load_file'), patch('kivy.app.App.get_running_app'):
    from services.connection.main_conn.connection_manager import ConnectionManager

class TestVersionHandshake(unittest.TestCase):
    def setUp(self):
        # We need to mock get_running_app for the actual test execution
        self.mock_app = MagicMock()
        self.patcher_app = patch('kivy.app.App.get_running_app', return_value=self.mock_app)
        self.patcher_app.start()

        self.mock_parent = MagicMock()
        self.mock_parent.ids = MagicMock()
        self.mock_parent.ids.label_servidor = MagicMock()
        self.mock_parent.ids.loading_spinner = MagicMock()
        
        self.manager = ConnectionManager(base_url="http://mock")

    def tearDown(self):
        self.patcher_app.stop()

    @patch('services.connection.main_conn.connection_manager.UrlRequest')
    @patch('version.__version__', '1.0.0')
    def test_version_too_old(self, mock_url_request):
        """Test that a popup is shown when the server version is newer than the client version."""
        
        # Mocking the success callback of UrlRequest
        def mock_init(url, on_success=None, **kwargs):
            # Simulate server response with version 1.1.0
            on_success(None, {"version": "1.1.0"})
            
        mock_url_request.side_effect = mock_init
        
        with patch.object(self.manager, '_show_update_popup') as mock_popup:
            with patch.object(self.manager, '_fetch_servers') as mock_fetch:
                self.manager._check_version(self.mock_parent)
                
                # 1. Verify popup was shown with the correct message
                mock_popup.assert_called_once()
                self.assertIn("1.1.0", mock_popup.call_args[0][0])
                self.assertIn("1.0.0", mock_popup.call_args[0][0])
                
                # 2. Verify servers were NOT fetched (flow stopped)
                mock_fetch.assert_not_called()
                
                # 3. Verify loading state was cleaned up
                self.assertFalse(self.mock_parent.loading)

    @patch('services.connection.main_conn.connection_manager.UrlRequest')
    @patch('version.__version__', '1.0.0')
    def test_version_compatible(self, mock_url_request):
        """Test that servers are fetched normally when versions are compatible."""
        
        def mock_init(url, on_success=None, **kwargs):
            # Simulate server response with matching version
            on_success(None, {"version": "1.0.0"})
            
        mock_url_request.side_effect = mock_init
        
        with patch.object(self.manager, '_show_update_popup') as mock_popup:
            with patch.object(self.manager, '_fetch_servers') as mock_fetch:
                self.manager._check_version(self.mock_parent)
                
                # 1. Verify popup was NOT shown
                mock_popup.assert_not_called()
                
                # 2. Verify it proceeded to fetch servers
                mock_fetch.assert_called_once()

    @patch('services.connection.main_conn.connection_manager.UrlRequest')
    def test_version_error_fallback(self, mock_url_request):
        """Test that if the version check fails, the app still allows proceeding (fail-safe)."""
        
        def mock_init(url, on_error=None, **kwargs):
            on_error(None, "Connection error")
            
        mock_url_request.side_effect = mock_init
        
        with patch.object(self.manager, '_fetch_servers') as mock_fetch:
            self.manager._check_version(self.mock_parent)
            
            # Should fallback to fetching servers anyway to not block the user
            mock_fetch.assert_called_once()

if __name__ == "__main__":
    unittest.main()
