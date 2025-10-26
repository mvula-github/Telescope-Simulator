#!/usr/bin/env python3
"""
Enhanced data display and viewing system for Telescope Simulator
Provides configurable display options and comprehensive data viewing capabilities
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from tabulate import tabulate
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from core.access_control import access_control_manager

# Load environment variables
load_dotenv()

class DisplayFormat(Enum):
    """Available display formats"""
    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    SUMMARY = "summary"
    DETAILED = "detailed"

class DataCategory(Enum):
    """Data categories for filtering"""
    TELESCOPE = "telescope"
    LOGS = "logs"
    USERS = "users"
    OBJECTS = "objects"
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"

class DataDisplayManager:
    """Manages data display options and viewing capabilities"""
    
    def __init__(self):
        self.display_config = self._load_display_config()
        self.mongo_client = None
        self.mongo_db = None
        self._init_mongodb()
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
            DB_NAME = os.getenv('DB_NAME', 'celestiCodeServerDB')
            
            self.mongo_client = MongoClient(MONGO_URI)
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[DB_NAME]
            print("Data display manager connected to MongoDB")
        except Exception as e:
            print(f"Data display manager MongoDB connection failed: {e}")
            self.mongo_client = None
            self.mongo_db = None
    
    def _load_display_config(self) -> Dict[str, Any]:
        """Load display configuration from file or create default"""
        config_file = "Resources/display_config.json"
        
        default_config = {
            "default_format": "table",
            "table_style": "github",
            "max_rows": 100,
            "show_timestamps": True,
            "date_format": "%Y-%m-%d %H:%M:%S",
            "auto_refresh": False,
            "refresh_interval": 30,
            "color_output": True,
            "compact_mode": False,
            "show_headers": True,
            "export_path": "exports/",
            "filters": {
                "default_timeframe": 24,  # hours
                "default_levels": ["success", "error", "warning"],
                "default_categories": ["telescope", "system", "logs"]
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
            print(f"Warning: Could not load display config: {e}")
            return default_config
    
    def save_display_config(self):
        """Save current display configuration to file"""
        try:
            config_file = "Resources/display_config.json"
            with open(config_file, 'w') as f:
                json.dump(self.display_config, f, indent=2)
            print("Display configuration saved")
        except Exception as e:
            print(f"Error saving display config: {e}")
    
    def update_display_option(self, option: str, value: Any):
        """Update a display configuration option"""
        if option in self.display_config:
            self.display_config[option] = value
            self.save_display_config()
            print(f"Display option '{option}' updated to '{value}'")
        else:
            print(f"Unknown display option: {option}")
    
    def get_display_options(self) -> Dict[str, Any]:
        """Get current display options"""
        return self.display_config.copy()
    
    def display_telescope_data(self, format_type: str = None, filters: Dict[str, Any] = None, user: Dict[str, Any] = None) -> str:
        """Display telescope operational data"""
        if not self.mongo_db:
            return "Database connection not available"
        
        # Check permissions
        if user:
            has_permission, reason = access_control_manager.check_permission(user, "telescope_data", "view_data")
            if not has_permission:
                return f"Access denied: {reason}"
        
        format_type = format_type or self.display_config["default_format"]
        filters = filters or {}
        
        try:
            # Get telescope logs
            logs_collection = self.mongo_db['Logs']
            timeframe = filters.get('timeframe', self.display_config["filters"]["default_timeframe"])
            start_time = datetime.now() - timedelta(hours=timeframe)
            
            query = {
                'timestamp': {'$gte': start_time},
                'command': {'$in': ['Point to AltAz', 'Point To RaDec', 'Tracking', 'Rest Mode', 'Object Selection']}
            }
            
            if 'user' in filters:
                query['user'] = filters['user']
            
            if 'level' in filters:
                query['level'] = {'$in': filters['level']}
            
            logs = list(logs_collection.find(query).sort('timestamp', -1).limit(
                self.display_config["max_rows"]
            ))
            
            if not logs:
                return "No telescope data found for the specified criteria"
            
            return self._format_data(logs, format_type, "Telescope Operations")
            
        except PyMongoError as e:
            return f"Error retrieving telescope data: {e}"
    
    def display_system_logs(self, format_type: str = None, filters: Dict[str, Any] = None, user: Dict[str, Any] = None) -> str:
        """Display system logs with filtering options"""
        if not self.mongo_db:
            return "Database connection not available"
        
        # Check permissions
        if user:
            has_permission, reason = access_control_manager.check_permission(user, "system_logs", "view_data")
            if not has_permission:
                return f"Access denied: {reason}"
        
        format_type = format_type or self.display_config["default_format"]
        filters = filters or {}
        
        try:
            logs_collection = self.mongo_db['Logs']
            timeframe = filters.get('timeframe', self.display_config["filters"]["default_timeframe"])
            start_time = datetime.now() - timedelta(hours=timeframe)
            
            query = {'timestamp': {'$gte': start_time}}
            
            if 'user' in filters:
                query['user'] = filters['user']
            
            if 'level' in filters:
                query['level'] = {'$in': filters['level']}
            
            if 'command' in filters:
                query['command'] = {'$regex': filters['command'], '$options': 'i'}
            
            logs = list(logs_collection.find(query).sort('timestamp', -1).limit(
                self.display_config["max_rows"]
            ))
            
            if not logs:
                return "No system logs found for the specified criteria"
            
            # Filter data based on user permissions
            if user:
                logs = access_control_manager.filter_data_by_permissions(user, logs, "system_logs")
            
            return self._format_data(logs, format_type, "System Logs")
            
        except PyMongoError as e:
            return f"Error retrieving system logs: {e}"
    
    def display_user_activity(self, format_type: str = None, filters: Dict[str, Any] = None, user: Dict[str, Any] = None) -> str:
        """Display user activity summary"""
        if not self.mongo_db:
            return "Database connection not available"
        
        # Check permissions
        if user:
            has_permission, reason = access_control_manager.check_permission(user, "user_data", "view_data")
            if not has_permission:
                return f"Access denied: {reason}"
        
        format_type = format_type or self.display_config["default_format"]
        filters = filters or {}
        
        try:
            logs_collection = self.mongo_db['Logs']
            timeframe = filters.get('timeframe', self.display_config["filters"]["default_timeframe"])
            start_time = datetime.now() - timedelta(hours=timeframe)
            
            # Aggregate user activity
            pipeline = [
                {'$match': {'timestamp': {'$gte': start_time}}},
                {'$group': {
                    '_id': '$user',
                    'total_actions': {'$sum': 1},
                    'successful_actions': {'$sum': {'$cond': [{'$in': ['$level', ['success', 'info']]}, 1, 0]}},
                    'failed_actions': {'$sum': {'$cond': [{'$in': ['$level', ['error', 'critical']]}, 1, 0]}},
                    'last_activity': {'$max': '$timestamp'},
                    'commands': {'$addToSet': '$command'}
                }},
                {'$sort': {'total_actions': -1}}
            ]
            
            if 'user' in filters:
                pipeline[0]['$match']['user'] = filters['user']
            
            results = list(logs_collection.aggregate(pipeline))
            
            if not results:
                return "No user activity found for the specified criteria"
            
            # Format results for display
            formatted_data = []
            for result in results:
                success_rate = (result['successful_actions'] / result['total_actions'] * 100) if result['total_actions'] > 0 else 0
                formatted_data.append({
                    'user': result['_id'],
                    'total_actions': result['total_actions'],
                    'successful': result['successful_actions'],
                    'failed': result['failed_actions'],
                    'success_rate': f"{success_rate:.1f}%",
                    'last_activity': result['last_activity'].strftime(self.display_config["date_format"]),
                    'unique_commands': len(result['commands'])
                })
            
            return self._format_data(formatted_data, format_type, "User Activity Summary")
            
        except PyMongoError as e:
            return f"Error retrieving user activity: {e}"
    
    def display_celestial_objects(self, format_type: str = None, filters: Dict[str, Any] = None, user: Dict[str, Any] = None) -> str:
        """Display celestial objects data"""
        if not self.mongo_db:
            return "Database connection not available"
        
        # Check permissions
        if user:
            has_permission, reason = access_control_manager.check_permission(user, "celestial_objects", "view_data")
            if not has_permission:
                return f"Access denied: {reason}"
        
        format_type = format_type or self.display_config["default_format"]
        filters = filters or {}
        
        try:
            objects_collection = self.mongo_db['Objects']
            query = {}
            
            if 'user_id' in filters:
                query['user_id'] = filters['user_id']
            
            if 'name' in filters:
                query['name'] = {'$regex': filters['name'], '$options': 'i'}
            
            objects = list(objects_collection.find(query).sort('name', 1))
            
            if not objects:
                return "No celestial objects found for the specified criteria"
            
            # Format objects data
            formatted_data = []
            for obj in objects:
                formatted_data.append({
                    'name': obj.get('name', 'N/A'),
                    'description': obj.get('description', 'N/A'),
                    'ra_dec': obj.get('ra_dec', 'N/A'),
                    'ned_code': obj.get('ned_code', 'N/A'),
                    'created_by': obj.get('user_id', 'N/A'),
                    'created_at': obj.get('created_at', 'N/A')
                })
            
            return self._format_data(formatted_data, format_type, "Celestial Objects")
            
        except PyMongoError as e:
            return f"Error retrieving celestial objects: {e}"
    
    def display_system_status(self, format_type: str = None, user: Dict[str, Any] = None) -> str:
        """Display current system status and configuration"""
        # Check permissions
        if user:
            has_permission, reason = access_control_manager.check_permission(user, "system_config", "view_data")
            if not has_permission:
                return f"Access denied: {reason}"
        
        format_type = format_type or self.display_config["default_format"]
        
        try:
            # Get system configuration
            from core.system_config import config
            
            status_data = {
                'telescope_location': {
                    'latitude': config.get('latitude', 'Not set'),
                    'longitude': config.get('longitude', 'Not set'),
                    'elevation': config.get('elevation', 'Not set')
                },
                'movement_limits': {
                    'altitude': config.get('altitude_limits', [0, 90]),
                    'azimuth': config.get('azimuth_limits', [0, 360])
                },
                'safety_settings': {
                    'prevent_below_horizon': config.get('prevent_below_horizon', True),
                    'safety_altitude_margin': config.get('safety_alt_margin_deg', 0.5),
                    'safety_azimuth_margin': config.get('safety_az_margin_deg', 1.0)
                },
                'movement_settings': {
                    'movement_timeout': config.get('movement_timeout', 10),
                    'position_tolerance': config.get('position_tolerance', 0.01),
                    'clamp_to_limits': config.get('clamp_to_limits', True)
                },
                'database_status': 'Connected' if self.mongo_db else 'Disconnected',
                'last_updated': datetime.now().strftime(self.display_config["date_format"])
            }
            
            return self._format_data([status_data], format_type, "System Status")
            
        except Exception as e:
            return f"Error retrieving system status: {e}"
    
    def _format_data(self, data: List[Dict[str, Any]], format_type: str, title: str) -> str:
        """Format data according to specified format type"""
        if not data:
            return f"No data available for {title}"
        
        if format_type == "table":
            return self._format_as_table(data, title)
        elif format_type == "json":
            return self._format_as_json(data, title)
        elif format_type == "summary":
            return self._format_as_summary(data, title)
        elif format_type == "detailed":
            return self._format_as_detailed(data, title)
        else:
            return self._format_as_table(data, title)  # Default to table
    
    def _format_as_table(self, data: List[Dict[str, Any]], title: str) -> str:
        """Format data as a table"""
        if not data:
            return f"No data available for {title}"
        
        # Convert data to list of lists for tabulate
        if isinstance(data[0], dict):
            headers = list(data[0].keys())
            rows = []
            for item in data:
                row = []
                for header in headers:
                    value = item.get(header, 'N/A')
                    if isinstance(value, datetime):
                        value = value.strftime(self.display_config["date_format"])
                    elif isinstance(value, (list, dict)):
                        value = str(value)
                    row.append(str(value))
                rows.append(row)
        else:
            headers = ["Data"]
            rows = [[str(item)] for item in data]
        
        table = tabulate(rows, headers=headers, tablefmt=self.display_config["table_style"])
        
        result = f"\n{'='*60}\n"
        result += f"{title.upper()}\n"
        result += f"{'='*60}\n"
        result += table
        result += f"\n{'='*60}\n"
        result += f"Total records: {len(data)}\n"
        
        return result
    
    def _format_as_json(self, data: List[Dict[str, Any]], title: str) -> str:
        """Format data as JSON"""
        result = f"\n{'='*60}\n"
        result += f"{title.upper()} (JSON FORMAT)\n"
        result += f"{'='*60}\n"
        result += json.dumps(data, indent=2, default=str)
        result += f"\n{'='*60}\n"
        return result
    
    def _format_as_summary(self, data: List[Dict[str, Any]], title: str) -> str:
        """Format data as a summary"""
        result = f"\n{'='*60}\n"
        result += f"{title.upper()} - SUMMARY\n"
        result += f"{'='*60}\n"
        result += f"Total records: {len(data)}\n"
        
        if data and isinstance(data[0], dict):
            # Show field statistics
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())
            
            result += f"Available fields: {', '.join(sorted(all_keys))}\n"
            
            # Show sample record
            if data:
                result += f"\nSample record:\n"
                sample = data[0]
                for key, value in sample.items():
                    if isinstance(value, datetime):
                        value = value.strftime(self.display_config["date_format"])
                    result += f"  {key}: {value}\n"
        
        result += f"{'='*60}\n"
        return result
    
    def _format_as_detailed(self, data: List[Dict[str, Any]], title: str) -> str:
        """Format data in detailed view"""
        result = f"\n{'='*80}\n"
        result += f"{title.upper()} - DETAILED VIEW\n"
        result += f"{'='*80}\n"
        
        for i, item in enumerate(data, 1):
            result += f"\nRecord {i}:\n"
            result += "-" * 40 + "\n"
            
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, datetime):
                        value = value.strftime(self.display_config["date_format"])
                    elif isinstance(value, (list, dict)):
                        value = json.dumps(value, indent=2, default=str)
                    result += f"{key:20}: {value}\n"
            else:
                result += f"Data: {item}\n"
        
        result += f"\n{'='*80}\n"
        result += f"Total records: {len(data)}\n"
        
        return result
    
    def export_data(self, data_type: str, format_type: str, filename: str = None, filters: Dict[str, Any] = None, user: Dict[str, Any] = None) -> str:
        """Export data to file"""
        try:
            # Check export permissions
            if user:
                has_permission, reason = access_control_manager.check_permission(user, data_type, "export_data")
                if not has_permission:
                    return f"Export denied: {reason}"
            
            # Get data based on type
            if data_type == "telescope":
                data_str = self.display_telescope_data(format_type, filters, user)
            elif data_type == "logs":
                data_str = self.display_system_logs(format_type, filters, user)
            elif data_type == "users":
                data_str = self.display_user_activity(format_type, filters, user)
            elif data_type == "objects":
                data_str = self.display_celestial_objects(format_type, filters, user)
            elif data_type == "system":
                data_str = self.display_system_status(format_type, user)
            else:
                return f"Unknown data type: {data_type}"
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{data_type}_data_{timestamp}.txt"
            
            # Ensure export directory exists
            export_dir = self.display_config["export_path"]
            os.makedirs(export_dir, exist_ok=True)
            
            filepath = os.path.join(export_dir, filename)
            
            # Write data to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data_str)
            
            return f"Data exported to {filepath}"
            
        except Exception as e:
            return f"Export failed: {e}"
    
    def get_available_data_types(self) -> List[str]:
        """Get list of available data types"""
        return ["telescope", "logs", "users", "objects", "system"]
    
    def get_available_formats(self) -> List[str]:
        """Get list of available display formats"""
        return [format_type.value for format_type in DisplayFormat]
    
    def close(self):
        """Close database connections"""
        if self.mongo_client:
            self.mongo_client.close()

# Global instance
data_display_manager = DataDisplayManager()
