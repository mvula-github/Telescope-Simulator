"""Resources package for configuration and data files"""

import os
import json

def get_config_path():
    """Get the path to the config file"""
    return os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    """Load configuration from JSON file"""
    try:
        with open(get_config_path(), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

__all__ = ['get_config_path', 'load_config']
