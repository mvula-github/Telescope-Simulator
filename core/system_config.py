import json
import os
import logging

# Path to the configuration file (JSON format)
CONFIG_FILE = os.path.join("Resources", "config.json")

class AppConfig:
    """
    Handles loading, saving, updating, and validating configuration from a JSON file.
    Provides methods to interact with configuration data for the telescope simulator.
    """
    def __init__(self, config_file=CONFIG_FILE):
        # Initialize with the config file path and load its data
        self.config_file = config_file
        self._data = self._load_config()

    def _load_config(self):
        # Load configuration data from the JSON file
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {self.config_file}. Using empty config.")
            return {}
        except json.JSONDecodeError as e:
            # If JSON is invalid, use an empty config
            logging.error(f"Error decoding JSON configuration: {e}")
            return {}

    def get(self, key, default=None):
        """Get a configuration value by key. Returns default if key is missing."""
        return self._data.get(key, default)
    
    def has(self, key):
        """Check if a configuration key exists."""
        return key in self._data
    
    def set(self, key, value):
        """Set a configuration value and save to file."""
        self._data[key] = value
        self._save_config()
    
    def save(self):
        """Save the current configuration to file."""
        self._save_config()

    def reload(self):
        """Reload the configuration from the file (refreshes _data)."""
        self._data = self._load_config()

    def update(self, key, value):
        """Update a specific configuration value and save to the file."""
        self._data[key] = value
        self._save_config()

    def _save_config(self):
        """Save the current configuration data to the file."""
        try:
            # Ensure the directory exists before saving
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(self._data, file, indent=4)
        except (IOError, OSError) as e:
            logging.error(f"Error saving configuration: {e}")

    def validate(self):
        """
        Validate the configuration data.
        Returns True if all required keys are present, False otherwise.
        """
        required_keys = [
            'latitude', 'longitude', 'elevation',
            'celestial_ping_time', 'altitude_limits', 'azimuth_limits'
        ]
        missing_keys = [key for key in required_keys if key not in self._data]
        if missing_keys:
            logging.error(f"Missing configuration keys: {missing_keys}")
            return False
        return True

# Instantiate a single config object for use throughout the application
config = AppConfig()