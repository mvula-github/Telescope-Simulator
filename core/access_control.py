#!/usr/bin/env python3
"""
Access control system for Telescope Simulator
Manages operator permissions and data access controls
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from functools import wraps

class PermissionLevel(Enum):
    """Permission levels for data access"""
    READ_ONLY = "read_only"
    OPERATOR = "operator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class DataAccess(Enum):
    """Data access types"""
    TELESCOPE_DATA = "telescope_data"
    SYSTEM_LOGS = "system_logs"
    USER_DATA = "user_data"
    CELESTIAL_OBJECTS = "celestial_objects"
    SYSTEM_CONFIG = "system_config"
    SECURITY_LOGS = "security_logs"
    EXPORT_DATA = "export_data"
    CONFIGURE_DISPLAY = "configure_display"

class AccessControlManager:
    """Manages access control and permissions for the telescope system"""
    
    def __init__(self):
        self.permissions_config = self._load_permissions_config()
        self.session_logs = []
        self.failed_attempts = {}
        self.lockout_threshold = 5
        self.lockout_duration = 15  # minutes
    
    def _load_permissions_config(self) -> Dict[str, Any]:
        """Load permissions configuration from file or create default"""
        config_file = "Resources/access_control.json"
        
        default_config = {
            "permissions": {
                "operator": {
                    "allowed_data": [
                        "telescope_data",
                        "system_logs",
                        "celestial_objects"
                    ],
                    "allowed_actions": [
                        "view_data",
                        "export_own_data"
                    ],
                    "restrictions": {
                        "max_export_size": 1000,
                        "timeframe_limit": 168,  # 1 week
                        "no_user_data_access": True,
                        "no_config_access": True
                    }
                },
                "admin": {
                    "allowed_data": [
                        "telescope_data",
                        "system_logs",
                        "user_data",
                        "celestial_objects",
                        "system_config"
                    ],
                    "allowed_actions": [
                        "view_data",
                        "export_data",
                        "configure_display",
                        "manage_users"
                    ],
                    "restrictions": {
                        "max_export_size": 10000,
                        "timeframe_limit": 8760,  # 1 year
                        "no_security_logs": True
                    }
                },
                "super_admin": {
                    "allowed_data": [
                        "telescope_data",
                        "system_logs",
                        "user_data",
                        "celestial_objects",
                        "system_config",
                        "security_logs"
                    ],
                    "allowed_actions": [
                        "view_data",
                        "export_data",
                        "configure_display",
                        "manage_users",
                        "manage_permissions",
                        "system_maintenance"
                    ],
                    "restrictions": {
                        "max_export_size": -1,  # Unlimited
                        "timeframe_limit": -1,  # Unlimited
                    }
                }
            },
            "security_settings": {
                "session_timeout": 30,  # minutes
                "max_concurrent_sessions": 3,
                "audit_all_actions": True,
                "require_reauthentication": False
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                # Create default config file
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            print(f"⚠️  Warning: Could not load access control config: {e}")
            return default_config
    
    def save_permissions_config(self):
        """Save current permissions configuration to file"""
        try:
            config_file = "Resources/access_control.json"
            with open(config_file, 'w') as f:
                json.dump(self.permissions_config, f, indent=2)
            print("✅ Access control configuration saved")
        except Exception as e:
            print(f"❌ Error saving access control config: {e}")
    
    def check_permission(self, user: Dict[str, Any], data_type: str, action: str = "view_data") -> Tuple[bool, str]:
        """
        Check if user has permission to access specific data or perform action
        
        Args:
            user: User information dictionary
            data_type: Type of data being accessed
            action: Action being performed
            
        Returns:
            Tuple of (has_permission, reason)
        """
        try:
            username = user.get('username', 'unknown')
            role = user.get('role', 'operator')
            
            # Check for account lockout
            if self._is_user_locked_out(username):
                return False, f"Account temporarily locked due to failed attempts"
            
            # Get user permissions
            user_permissions = self.permissions_config["permissions"].get(role, {})
            if not user_permissions:
                return False, f"Unknown role: {role}"
            
            # Check if data type is allowed
            allowed_data = user_permissions.get("allowed_data", [])
            if data_type not in allowed_data:
                return False, f"Access denied: {data_type} not allowed for role {role}"
            
            # Check if action is allowed
            allowed_actions = user_permissions.get("allowed_actions", [])
            if action not in allowed_actions:
                return False, f"Action denied: {action} not allowed for role {role}"
            
            # Log successful access
            self._log_access(username, data_type, action, True, "Access granted")
            
            return True, "Access granted"
            
        except Exception as e:
            self._log_access(username, data_type, action, False, f"Error checking permissions: {e}")
            return False, f"Error checking permissions: {e}"
    
    def check_export_permission(self, user: Dict[str, Any], data_type: str, record_count: int) -> Tuple[bool, str]:
        """Check if user can export data with given record count"""
        try:
            username = user.get('username', 'unknown')
            role = user.get('role', 'operator')
            
            # Check basic export permission
            has_permission, reason = self.check_permission(user, data_type, "export_data")
            if not has_permission:
                return False, reason
            
            # Check export size limits
            user_permissions = self.permissions_config["permissions"].get(role, {})
            restrictions = user_permissions.get("restrictions", {})
            max_export_size = restrictions.get("max_export_size", 1000)
            
            if max_export_size > 0 and record_count > max_export_size:
                return False, f"Export size limit exceeded: {record_count} > {max_export_size}"
            
            return True, "Export allowed"
            
        except Exception as e:
            return False, f"Error checking export permissions: {e}"
    
    def check_timeframe_permission(self, user: Dict[str, Any], hours: int) -> Tuple[bool, str]:
        """Check if user can access data for given timeframe"""
        try:
            role = user.get('role', 'operator')
            user_permissions = self.permissions_config["permissions"].get(role, {})
            restrictions = user_permissions.get("restrictions", {})
            timeframe_limit = restrictions.get("timeframe_limit", 168)
            
            if timeframe_limit > 0 and hours > timeframe_limit:
                return False, f"Timeframe limit exceeded: {hours}h > {timeframe_limit}h"
            
            return True, "Timeframe allowed"
            
        except Exception as e:
            return False, f"Error checking timeframe permissions: {e}"
    
    def filter_data_by_permissions(self, user: Dict[str, Any], data: List[Dict[str, Any]], data_type: str) -> List[Dict[str, Any]]:
        """Filter data based on user permissions"""
        try:
            role = user.get('role', 'operator')
            user_permissions = self.permissions_config["permissions"].get(role, {})
            restrictions = user_permissions.get("restrictions", {})
            
            filtered_data = data.copy()
            
            # Apply role-specific filters
            if restrictions.get("no_user_data_access", False):
                # Remove user-specific data for operators
                for item in filtered_data:
                    if 'user' in item:
                        item['user'] = '[REDACTED]'
                    if 'user_id' in item:
                        item['user_id'] = '[REDACTED]'
            
            if restrictions.get("no_config_access", False):
                # Remove configuration data for operators
                filtered_data = [item for item in filtered_data if not any(
                    key.startswith('config_') or key in ['settings', 'configuration'] 
                    for key in item.keys()
                )]
            
            return filtered_data
            
        except Exception as e:
            print(f"⚠️  Warning: Error filtering data: {e}")
            return data
    
    def _is_user_locked_out(self, username: str) -> bool:
        """Check if user is currently locked out"""
        if username not in self.failed_attempts:
            return False
        
        attempts = self.failed_attempts[username]
        if len(attempts) < self.lockout_threshold:
            return False
        
        # Check if lockout period has expired
        last_attempt = max(attempts)
        if datetime.now() - last_attempt > timedelta(minutes=self.lockout_duration):
            # Clear expired attempts
            self.failed_attempts[username] = []
            return False
        
        return True
    
    def _log_access(self, username: str, data_type: str, action: str, success: bool, reason: str):
        """Log access attempt"""
        log_entry = {
            'timestamp': datetime.now(),
            'username': username,
            'data_type': data_type,
            'action': action,
            'success': success,
            'reason': reason,
            'ip_address': 'localhost'  # In a real system, this would be the actual IP
        }
        
        self.session_logs.append(log_entry)
        
        # Track failed attempts
        if not success:
            if username not in self.failed_attempts:
                self.failed_attempts[username] = []
            self.failed_attempts[username].append(datetime.now())
            
            # Clean old attempts (older than lockout duration)
            cutoff = datetime.now() - timedelta(minutes=self.lockout_duration)
            self.failed_attempts[username] = [
                attempt for attempt in self.failed_attempts[username] 
                if attempt > cutoff
            ]
        
        # Keep only recent logs (last 1000 entries)
        if len(self.session_logs) > 1000:
            self.session_logs = self.session_logs[-1000:]
    
    def get_user_permissions_summary(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of user permissions"""
        try:
            role = user.get('role', 'operator')
            user_permissions = self.permissions_config["permissions"].get(role, {})
            
            return {
                'role': role,
                'allowed_data': user_permissions.get("allowed_data", []),
                'allowed_actions': user_permissions.get("allowed_actions", []),
                'restrictions': user_permissions.get("restrictions", {}),
                'is_locked_out': self._is_user_locked_out(user.get('username', 'unknown'))
            }
        except Exception as e:
            return {'error': f"Error getting permissions: {e}"}
    
    def get_security_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security-related logs"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            log for log in self.session_logs 
            if log['timestamp'] > cutoff_time and not log['success']
        ]
    
    def update_permissions(self, role: str, permissions: Dict[str, Any]) -> bool:
        """Update permissions for a role (admin only)"""
        try:
            if role in self.permissions_config["permissions"]:
                self.permissions_config["permissions"][role].update(permissions)
                self.save_permissions_config()
                return True
            return False
        except Exception as e:
            print(f"❌ Error updating permissions: {e}")
            return False
    
    def require_permission(self, data_type: str, action: str = "view_data"):
        """Decorator to require specific permissions"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user from arguments (assuming it's the first argument after self)
                user = None
                for arg in args:
                    if isinstance(arg, dict) and 'username' in arg:
                        user = arg
                        break
                
                if not user:
                    return "❌ User information not found"
                
                has_permission, reason = self.check_permission(user, data_type, action)
                if not has_permission:
                    return f"❌ Access denied: {reason}"
                
                return func(*args, **kwargs)
            return wrapper
        return decorator

# Global instance
access_control_manager = AccessControlManager()

# Permission decorators for common use cases
require_telescope_data = access_control_manager.require_permission("telescope_data")
require_system_logs = access_control_manager.require_permission("system_logs")
require_user_data = access_control_manager.require_permission("user_data")
require_export_permission = access_control_manager.require_permission("export_data", "export_data")
