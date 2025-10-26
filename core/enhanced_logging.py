#!/usr/bin/env python3
"""
Enhanced logging system for Telescope Simulator
"""

import os
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class LogLevel(Enum):
    """Enhanced log levels"""
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"
    AUDIT = "audit"

class LogCategory(Enum):
    """Log categories for better organization"""
    AUTHENTICATION = "auth"
    TELESCOPE_MOVEMENT = "telescope"
    USER_MANAGEMENT = "user_mgmt"
    OBJECT_TRACKING = "object_tracking"
    SYSTEM_CONFIG = "system_config"
    COORDINATE_CONVERSION = "coordinates"
    SIMULATION = "simulation"
    DATABASE = "database"
    SECURITY = "security"
    GENERAL = "general"

class EnhancedLogger:
    """Enhanced logging system with multiple outputs and better structure"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.file_logger = None
        self.console_logger = None
        self._init_logging()
    
    def _init_logging(self):
        """Initialize all logging components"""
        self._init_mongodb()
        self._init_file_logging()
        self._init_console_logging()
    
    def _init_mongodb(self):
        """Initialize MongoDB logging"""
        try:
            MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
            DB_NAME = os.getenv('DB_NAME', 'celestiCodeServerDB')
            
            self.mongo_client = MongoClient(MONGO_URI)
            self.mongo_client.admin.command('ping')  # Test connection
            self.mongo_db = self.mongo_client[DB_NAME]
            self.mongo_collection = self.mongo_db['enhanced_logs']
            
            # Create indexes for better performance
            self.mongo_collection.create_index([('timestamp', -1)], background=True)
            self.mongo_collection.create_index([('level', 1), ('timestamp', -1)], background=True)
            self.mongo_collection.create_index([('category', 1), ('timestamp', -1)], background=True)
            self.mongo_collection.create_index([('user', 1), ('timestamp', -1)], background=True)
            
            print("Enhanced MongoDB logging initialized")
        except Exception as e:
            print(f"MongoDB logging unavailable: {e}")
            self.mongo_client = None
            self.mongo_db = None
            self.mongo_collection = None
    
    def _init_file_logging(self):
        """Initialize file-based logging"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # Configure file logger
            self.file_logger = logging.getLogger('telescope_file')
            self.file_logger.setLevel(logging.DEBUG)
            
            # Create file handler with rotation
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'telescope.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.file_logger.addHandler(file_handler)
            
            print("File logging initialized")
        except Exception as e:
            print(f"File logging unavailable: {e}")
            self.file_logger = None
    
    def _init_console_logging(self):
        """Initialize console logging"""
        try:
            self.console_logger = logging.getLogger('telescope_console')
            self.console_logger.setLevel(logging.INFO)
            
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Create colored formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.console_logger.addHandler(console_handler)
            
            print("Console logging initialized")
        except Exception as e:
            print(f"Console logging unavailable: {e}")
    
    def log(self, 
            level: LogLevel, 
            category: LogCategory, 
            message: str, 
            user: Optional[str] = None,
            command: Optional[str] = None,
            extra_data: Optional[Dict[str, Any]] = None,
            exception: Optional[Exception] = None):
        """
        Enhanced logging function with multiple outputs
        
        Args:
            level: Log level (DEBUG, INFO, SUCCESS, etc.)
            category: Log category (AUTHENTICATION, TELESCOPE_MOVEMENT, etc.)
            message: Log message
            user: Username (if applicable)
            command: Command being executed (if applicable)
            extra_data: Additional structured data
            exception: Exception object (if logging an error)
        """
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.now(),
            'level': level.value,
            'category': category.value,
            'message': message,
            'user': user,
            'command': command,
            'extra_data': extra_data or {},
            'exception': str(exception) if exception else None,
            'session_id': self._get_session_id()
        }
        
        # Log to MongoDB
        self._log_to_mongodb(log_entry)
        
        # Log to file
        self._log_to_file(log_entry)
        
        # Log to console (for important messages)
        self._log_to_console(log_entry)
    
    def _log_to_mongodb(self, log_entry: Dict[str, Any]):
        """Log to MongoDB"""
        if self.mongo_collection is not None:
            try:
                self.mongo_collection.insert_one(log_entry)
            except PyMongoError as e:
                print(f"MongoDB logging failed: {e}")
    
    def _log_to_file(self, log_entry: Dict[str, Any]):
        """Log to file"""
        if self.file_logger is not None:
            try:
                log_message = f"{log_entry['message']}"
                if log_entry['user']:
                    log_message += f" [User: {log_entry['user']}]"
                if log_entry['command']:
                    log_message += f" [Command: {log_entry['command']}]"
                if log_entry['extra_data']:
                    log_message += f" [Data: {json.dumps(log_entry['extra_data'])}]"
                
                # Map our levels to Python logging levels
                python_level = self._map_to_python_level(log_entry['level'])
                self.file_logger.log(python_level, log_message)
            except Exception as e:
                print(f"File logging failed: {e}")
    
    def _log_to_console(self, log_entry: Dict[str, Any]):
        """Log to console for important messages"""
        if self.console_logger is not None and log_entry['level'] in ['error', 'critical', 'security', 'warning']:
            try:
                log_message = f"[{log_entry['category'].upper()}] {log_entry['message']}"
                if log_entry['user']:
                    log_message += f" (User: {log_entry['user']})"
                
                python_level = self._map_to_python_level(log_entry['level'])
                self.console_logger.log(python_level, log_message)
            except Exception as e:
                print(f"Console logging failed: {e}")
    
    def _map_to_python_level(self, level: str) -> int:
        """Map our log levels to Python logging levels"""
        mapping = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'success': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
            'security': logging.CRITICAL,
            'audit': logging.INFO
        }
        return mapping.get(level, logging.INFO)
    
    def _get_session_id(self) -> str:
        """Generate or retrieve session ID"""
        # Simple session ID based on timestamp
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Convenience methods for common log types
    def log_auth(self, level: LogLevel, message: str, user: str = None, success: bool = True):
        """Log authentication events"""
        extra_data = {'success': success}
        self.log(level, LogCategory.AUTHENTICATION, message, user, extra_data=extra_data)
    
    def log_telescope(self, level: LogLevel, message: str, user: str = None, command: str = None, coordinates: Dict = None):
        """Log telescope movement events"""
        extra_data = {'coordinates': coordinates} if coordinates else {}
        self.log(level, LogCategory.TELESCOPE_MOVEMENT, message, user, command, extra_data)
    
    def log_user_mgmt(self, level: LogLevel, message: str, user: str = None, target_user: str = None):
        """Log user management events"""
        extra_data = {'target_user': target_user} if target_user else {}
        self.log(level, LogCategory.USER_MANAGEMENT, message, user, extra_data=extra_data)
    
    def log_security(self, level: LogLevel, message: str, user: str = None, ip_address: str = None):
        """Log security events"""
        extra_data = {'ip_address': ip_address} if ip_address else {}
        self.log(level, LogCategory.SECURITY, message, user, extra_data=extra_data)
    
    def log_system(self, level: LogLevel, message: str, component: str = None):
        """Log system events"""
        extra_data = {'component': component} if component else {}
        self.log(level, LogCategory.SYSTEM_CONFIG, message, extra_data=extra_data)

# Global logger instance
logger = EnhancedLogger()

# Convenience functions for backward compatibility
def write_log(user: str, command: str, level: str, description: str):
    """Backward compatible logging function"""
    try:
        log_level = LogLevel(level.lower())
        log_category = LogCategory.GENERAL
        logger.log(log_level, log_category, description, user, command)
    except ValueError:
        # Fallback to info level for unknown levels
        logger.log(LogLevel.INFO, LogCategory.GENERAL, description, user, command)

def log_success(user: str, command: str, message: str, extra_data: Dict = None):
    """Log success events"""
    logger.log(LogLevel.SUCCESS, LogCategory.GENERAL, message, user, command, extra_data)

def log_error(user: str, command: str, message: str, exception: Exception = None, extra_data: Dict = None):
    """Log error events"""
    logger.log(LogLevel.ERROR, LogCategory.GENERAL, message, user, command, extra_data, exception)

def log_warning(user: str, command: str, message: str, extra_data: Dict = None):
    """Log warning events"""
    logger.log(LogLevel.WARNING, LogCategory.GENERAL, message, user, command, extra_data)

def log_info(user: str, command: str, message: str, extra_data: Dict = None):
    """Log info events"""
    logger.log(LogLevel.INFO, LogCategory.GENERAL, message, user, command, extra_data)

def log_debug(user: str, command: str, message: str, extra_data: Dict = None):
    """Log debug events"""
    logger.log(LogLevel.DEBUG, LogCategory.GENERAL, message, user, command, extra_data)

def log_security_event(user: str, message: str, ip_address: str = None):
    """Log security events"""
    logger.log_security(LogLevel.SECURITY, message, user, ip_address)

def log_audit(user: str, action: str, details: str):
    """Log audit events"""
    logger.log(LogLevel.AUDIT, LogCategory.SECURITY, f"{action}: {details}", user, action)

if __name__ == "__main__":
    # Test the enhanced logging system
    logger.log_info("test_user", "test_command", "Testing enhanced logging system")
    logger.log_auth(LogLevel.SUCCESS, "User logged in successfully", "admin")
    logger.log_telescope(LogLevel.INFO, "Telescope moved to coordinates", "admin", "move_tel", {"alt": 45, "az": 180})
    logger.log_security(LogLevel.WARNING, "Multiple failed login attempts", "admin")
    print("Enhanced logging system test completed")
