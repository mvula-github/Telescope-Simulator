"""Simulation package for CoppeliaSim integration and object tracking"""

# Import all simulation modules
from . import sim_interface
from . import track_objects
from . import sim_const

# Make key functions easily accessible
from .track_objects import create_object, list_objects, update_object, delete_object, objects_collection

__all__ = [
    'sim_interface',
    'track_objects',
    'sim_const',
    'create_object',
    'list_objects', 
    'update_object',
    'delete_object',
    'objects_collection'
]
