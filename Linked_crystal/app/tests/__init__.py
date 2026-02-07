
import os
import sys
from unittest.mock import patch

# Configure Kivy for headless testing
os.environ['KIVY_NO_CONSOLELOG'] = '1'
os.environ['KIVY_NO_ARGS'] = '1'

# We apply a global patch to Builder.load_file to prevent FileNotFoundError
# during module imports in tests.
load_file_patcher = patch('kivy.lang.Builder.load_file')
load_file_patcher.start()

# Prevent Kivy from opening windows
try:
    from kivy.config import Config
    Config.set('graphics', 'backend', 'headless')
except ImportError:
    pass

# Ensure src is in path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
