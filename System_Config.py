import json
import os

CONFIG_FILE = os.path.join("Resources", "config.json")

class Config:
    """
    Handles loading, saving, updating, and validating configuration from a JSON file.
    """
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self._data = self._load_config()

    def _load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Configuration file not found: {self.config_file}. Using empty config.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON configuration: {e}")
            return {}

    def get(self, key, default=None):
        """Get a configuration value by key."""
        return self._data.get(key, default)

    def reload(self):
        """Reload the configuration from the file."""
        self._data = self._load_config()

    def update(self, key, value):
        """Update a specific configuration value and save to the file."""
        self._data[key] = value
        self._save_config()

    def _save_config(self):
        """Save the current configuration data to the file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(self._data, file, indent=4)
        except IOError as e:
            print(f"Error saving configuration: {e}")

    def validate(self):
        """
        Validate the configuration data.
        Returns True if all required keys are present, False otherwise.
        """
        required_keys = [
            'latitude', 'longitude', 'elevation',
            'time_to_wait', 'altitude_limits', 'azimuth_limits'
        ]
        missing_keys = [key for key in required_keys if key not in self._data]
        if missing_keys:
            print(f"Missing configuration keys: {missing_keys}")
            return False
        return True

config = Config()  # Instantiate a single Config object