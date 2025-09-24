"""Core business logic package for telescope operations"""

# Import all core modules for easy access
from . import telescope_control
from . import calculations
from . import system_config
from . import file_handling
from . import system_checks

# Make key functions easily accessible
from .telescope_control import move_tel, telescope_rest, track_celestial_object
from .calculations import convert_radec_to_altaz, convert_altaz_to_radec
from .system_config import config
from .file_handling import write_log, display_logs, init_mongodb
from .system_checks import check_internet_connection

__all__ = [
    'telescope_control',
    'calculations', 
    'system_config',
    'file_handling',
    'system_checks',
    'move_tel',
    'telescope_rest',
    'track_celestial_object',
    'convert_radec_to_altaz',
    'convert_altaz_to_radec',
    'config',
    'write_log',
    'display_logs',
    'init_mongodb',
    'check_internet_connection'
]
