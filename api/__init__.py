"""API package for external interfaces and user management"""

# Import API modules
from . import user_api

# Make key functions easily accessible
from .user_api import create_user, list_users, update_user, delete_user, users_collection

__all__ = [
    'user_api',
    'create_user',
    'list_users',
    'update_user', 
    'delete_user',
    'users_collection'
]
