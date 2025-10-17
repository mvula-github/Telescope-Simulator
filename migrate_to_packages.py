# migrate_to_packages.py
import os
import shutil
import re

def create_directory_structure():
    """Create the new directory structure"""
    directories = [
        'core',
        'simulation', 
        'api',
        'ui/cli',
        'ui/web',
        'resources/data',
        'docs/api'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Create __init__.py in each directory
        init_file = os.path.join(directory, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write(f'"""Package: {directory}"""\n')
        print(f"Created directory: {directory}")

def move_files():
    """Move files to their new locations"""
    file_moves = {
        'Telescope_Movement.py': 'core/telescope_control.py',
        'Calculations.py': 'core/calculations.py',
        'System_Config.py': 'core/system_config.py',
        'File_Handling.py': 'core/file_handling.py',
        'System_Checks.py': 'core/system_checks.py',
        'sim.py': 'simulation/sim_interface.py',
        'simConst.py': 'simulation/sim_const.py',
        'Track_Objects.py': 'simulation/track_objects.py',
        'user_management.py': 'api/user_api.py',
        'testing.py': 'tests/integration_test.py'
    }
    
    for old_path, new_path in file_moves.items():
        if os.path.exists(old_path):
            # Create target directory if it doesn't exist
            target_dir = os.path.dirname(new_path)
            os.makedirs(target_dir, exist_ok=True)
            
            shutil.move(old_path, new_path)
            print(f"Moved {old_path} -> {new_path}")

def create_package_init_files():
    """Create proper __init__.py files for each package"""
    
    # Main package __init__.py
    main_init = '''"""
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
'''
    
    with open('__init__.py', 'w') as f:
        f.write(main_init)
    
    # Core package __init__.py
    core_init = '''"""Core business logic package for telescope operations"""

try:
    from .telescope_control import *
    from .calculations import *
    from .system_config import *
    from .file_handling import *
    from .system_checks import *
except ImportError:
    pass
'''
    
    with open('core/__init__.py', 'w') as f:
        f.write(core_init)
    
    # Simulation package __init__.py
    sim_init = '''"""Simulation package for CoppeliaSim integration and object tracking"""

try:
    from .sim_interface import *
    from .track_objects import *
    from .sim_const import *
except ImportError:
    pass
'''
    
    with open('simulation/__init__.py', 'w') as f:
        f.write(sim_init)
    
    # API package __init__.py
    api_init = '''"""API package for external interfaces and user management"""

try:
    from .user_api import *
except ImportError:
    pass
'''
    
    with open('api/__init__.py', 'w') as f:
        f.write(api_init)
    
    # Resources package __init__.py
    resources_init = '''"""Resources package for configuration and data files"""

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
'''
    
    with open('resources/__init__.py', 'w') as f:
        f.write(resources_init)

def main():
    """Run the complete migration"""
    print("�� Starting Telescope Simulator Package Migration...")
    
    print("\n📁 Creating directory structure...")
    create_directory_structure()
    
    print("\n📦 Creating package init files...")
    create_package_init_files()
    
    print("\n�� Moving files to new structure...")
    move_files()
    
    print("\n✅ Migration complete!")
    print("\n📋 Next steps:")
    print("1. Test your imports: python -c 'from core.telescope_control import *'")
    print("2. Update your main.py imports")
    print("3. Run your application to verify everything works")
    print("4. Consider adding a web interface in ui/web/")

if __name__ == "__main__":
    main()