"""
Telescope Simulator Package
A comprehensive telescope control and simulation system for educational and research purposes.
"""

__version__ = "1.0.0"
__author__ = "NWU Telescope Simulator Team"

# Import main modules for easy access
try:
    from .core.telescope_control import TelescopeController
    from .core.calculations import CoordinateConverter
    from .core.system_config import ConfigManager
except ImportError:
    # Fallback for development
    pass

__all__ = [
    'TelescopeController',
    'CoordinateConverter', 
    'ConfigManager'
]
