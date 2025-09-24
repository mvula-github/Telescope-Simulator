# main_new.py (updated version with proper imports)
import getpass
import logging
import time
from enum import Enum
from typing import Optional, Tuple
import re
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

# Add current directory to Python path for development
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import from new package structure
try:
    import core.file_handling as FH
    import core.telescope_control as TM
    import core.calculations as C
    import core.system_checks as SCh
    from core.system_config import config
    import simulation.track_objects as OT
    import api.user_api as UM
    from api.user_api import users_collection
    from users.middleware.auth import authenticate_user
    
    print("✅ Successfully imported from new package structure!")
    
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("🔄 Falling back to old imports...")
    
    # Fallback to old imports (in case migration isn't complete)
    import File_Handling as FH
    import Telescope_Movement as TM
    import Calculations as C
    import System_Checks as SCh
    from System_Config import config
    from simulation.track_objects import create_object, list_objects, update_object, delete_object, objects_collection
    from api.user_api import create_user, list_users, update_user, delete_user, users_collection
    from users.middleware.auth import authenticate_user

# Load .env
load_dotenv()

# Configure application logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Command descriptions for display
COMMAND_DESCRIPTIONS = {
    "Telescope Control": "Display menu responsible for telescope control functions.",
    "Configure Settings": "Display menu responsible for configuration settings (Admin only).",
    "Coordinate System": "Display menu responsible for coordinate calculations and conversions (Admin only).",
    "User Management": "Display menu for managing users (Admin only).",
    "Display Data": "Display menu responsible for displaying system info.",
    "Exit": "Exit the RTOS program.",
    "Point to AltAz": "Point telescope to specific Alt (altitude) & Az (azimuth) degrees.",
    "Point To RaDec": "Point telescope to specific Ra (right ascension) & Dec (declination) values.",
    "Tracking": "Initiate tracking process to track a celestial object.",
    "Rest Mode": "Move telescope to rest mode (facing straight up).",
    "Change Telescope Location": "Change physical location values of telescope (Latitude, Longitude, Elevation).",
    "Change Data Store Location": "Change the location where the telescope frequency data is stored.",
    "Change Telescope Limits": "Change upper and lower altitude and azimuth degree limits of telescope limits.",
    "Convert Alt & Az to Ra & Dec": "Convert Alt (altitude) & Az (azimuth) degrees to Ra (right ascension) & Dec (declination) values.",
    "Convert Ra & Dec to Alt & Az": "Convert Ra (right ascension) & Dec (declination) values to Alt (altitude) & Az (azimuth) degrees.",
    "Display location": "Display location using IP, GPS, and the last stored location in the configuration file.",
    "Display Telescope Logs": "Display log entries from MongoDB.",
    "Display All Commands & Descriptions": "Display list of all commands in program and their descriptions.",
    "Display Available Celestial Objects": "Display list of all celestial objects that are in a certain radius from ra (right ascension) & dec (declination) values.",
    "Check Internet Connection": "Test internet connection and give feedback.",
    "Create User": "Create a new user.",
    "List Users": "List all users.",
    "Update User": "Update an existing user.",
    "Delete User": "Delete an existing user."
}

# Menu options for each menu ID
MENUS = {
    0: {
        'admin': [
            "1. Telescope Control",
            "2. Configure Settings",
            "3. Coordinate System",
            "4. User Management",
            "5. Display Data",
            "6. Object Management",
            "7. Exit"
        ],
        'operator': [
            "1. Telescope Control",
            "2. Display Data",
            "3. Exit"
        ]
    },
    1: ["1. Point To AltAz", "2. Point To RaDec", "3. Tracking", "4. Rest Mode", "5. Objects", "6. Back"],
    2: ["1. Change Telescope Location", "2. Change Data Store Location", "3. Change Telescope Limits", "4. Back"],
    3: ["1. Convert Alt & Az to Ra & Dec", "2. Convert Ra & Dec to Alt & Az", "3. Back"],
    4: ["1. Create User", "2. List Users", "3. Update User", "4. Delete User", "5. Back"],
    5: ["1. Display Location", "2. Display Telescope Logs", "3. Display All Commands & Descriptions", 
        "4. Display Available Celestial Objects", "5. Check Internet Connection", "6. Back"],
    6: ["1. Create Object", "2. List Objects", "3. Update Object", "4. Delete Object", "5. Back"],
    7: ["Select an object by number, or type 0 to go back."]
}

# Menu enumeration
class Menu(Enum):
    MAIN = 0
    TELESCOPE = 1
    CONFIG = 2
    COORDS = 3
    USER_MANAGEMENT = 4
    DISPLAY = 5
    OBJECT_MANAGEMENT = 6
    OBJECTS = 7

# Authenticate user against Users collection with retry limit
def authenticate() -> Optional[dict]:
    # Create a function to get user by username (outside the loop)
    def get_user_by_username(username):
        try:
            if users_collection is None:
                print("❌ Database connection not available")
                return None
            return users_collection.find_one({"username": username})
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            username = input("Enter username: ")
            password = getpass.getpass("Enter password: ")
            
            # Debug: Test user lookup first
            test_user = get_user_by_username(username)
            if test_user is None:
                print(f"❌ User '{username}' not found in database")
                if attempt < max_attempts - 1:
                    print(f"Attempt {attempt + 1} of {max_attempts}. Try again.")
                continue
            
            token, error = authenticate_user(username, password, get_user_by_username)
            if token:
                # Get the user data for the response
                user = get_user_by_username(username)
                if user:
                    user['token'] = token  # Add token to user data
                    print(f"Welcome, {user['username']}!")
                    return user
            else:
                print(f"Authentication failed: {error}")
                if attempt < max_attempts - 1:
                    print(f"Attempt {attempt + 1} of {max_attempts}. Try again.")
        except KeyboardInterrupt:
            print("\nAuthentication cancelled.")
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            if attempt < max_attempts - 1:
                print(f"Attempt {attempt + 1} of {max_attempts}. Try again.")
    
    print("Maximum authentication attempts reached.")
    return None

# Handle menu choices and return the next menu or None to stay in current
def handle_menu_choice(current_menu: Menu, choice: int, user: dict) -> Optional[Menu]:
    username = user['username']
    role = user.get('role', 'operator')
    
    if current_menu == Menu.MAIN:
        if choice == 1:  # Telescope Control
            return Menu.TELESCOPE
        elif choice == 2 and role == 'admin':  # Configure Settings
            return Menu.CONFIG
        elif choice == 3 and role == 'admin':  # Coordinate System
            return Menu.COORDS
        elif choice == 4 and role == 'admin':  # User Management
            return Menu.USER_MANAGEMENT
        elif choice == 5:  # Display Data
            return Menu.DISPLAY
        elif choice == 6 and role == 'admin':  # Object Management
            return Menu.OBJECT_MANAGEMENT
        elif choice == 7:  # Exit
            return None
        else:
            print("Invalid choice or insufficient permissions")
            return None
    elif current_menu == Menu.TELESCOPE:
        if choice == 1:  # Point to AltAz
            try:
                alt, az = get_valid_alt_az()
                TM.move_tel(alt, az)
                print(f"Telescope moved to Alt: {alt}, Az: {az}")
                FH.write_log(username, "Point to AltAz", "success", f"Moved telescope to Alt: {alt}, Az: {az}")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Point to AltAz", "error", str(e))
        elif choice == 2:  # Point to RaDec
            try:
                ra, dec = get_valid_ra_dec()
                alt, az = C.convert_radec_to_altaz(ra, dec)
                TM.move_tel(alt, az)
                print(f"Telescope moved to RA: {ra}, Dec: {dec} (Alt: {alt}, Az: {az})")
                FH.write_log(username, "Point to RaDec", "success", f"Moved telescope to RA: {ra}, Dec: {dec}")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Point to RaDec", "error", str(e))
        elif choice == 3:  # Tracking
            try:
                code = get_valid_celestial_code()
                TM.track_celestial_object(code)
                FH.write_log(username, "Tracking", "success", f"Started tracking celestial object: {code}")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Tracking", "error", str(e))
        elif choice == 4:  # Rest Mode
            try:
                TM.telescope_rest(username)
                print("Telescope moved to rest position.")
                FH.write_log(username, "Rest Mode", "success", "Telescope moved to rest position")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Rest Mode", "error", str(e))
        elif choice == 5:  # Objects submenu
            return Menu.OBJECTS
        elif choice == 6:
            return Menu.MAIN
        return None
    elif current_menu == Menu.CONFIG:
        if choice == 1:  # Change Telescope Location
            try:
                change_telescope_location()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 2:  # Change Data Store Location
            try:
                change_data_store_location()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 3:  # Change Telescope Limits
            try:
                change_telescope_limits()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 4:
            return Menu.MAIN
        return None
    elif current_menu == Menu.COORDS:
        if choice == 1:  # Convert Alt & Az to Ra & Dec
            try:
                alt, az = get_valid_alt_az()
                ra, dec = C.convert_altaz_to_radec(alt, az)
                print(f"Alt: {alt}°, Az: {az}° -> RA: {ra:.6f} hours, Dec: {dec:.6f}°")
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 2:  # Convert Ra & Dec to Alt & Az
            try:
                ra, dec = get_valid_ra_dec()
                alt, az = C.convert_radec_to_altaz(ra, dec)
                print(f"RA: {ra}, Dec: {dec} -> Alt: {alt:.2f}°, Az: {az:.2f}°")
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 3:
            return Menu.MAIN
        return None
    elif current_menu == Menu.USER_MANAGEMENT:
        if choice == 1:  # Create User
            try:
                create_user()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 2:  # List Users
            try:
                list_users()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 3:  # Update User
            try:
                update_user()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 4:  # Delete User
            try:
                delete_user()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 5:
            return Menu.MAIN
        return None
    elif current_menu == Menu.DISPLAY:
        if choice == 1:  # Display Location
            try:
                display_location()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 2:  # Display Telescope Logs
            try:
                FH.display_logs()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 3:  # Display All Commands & Descriptions
            try:
                display_all_commands()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 4:  # Display Available Celestial Objects
            try:
                display_available_celestial_objects()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 5:  # Check Internet Connection
            try:
                status, message = SCh.check_internet_connection()
                print(f"Internet Connection: {message}")
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 6:
            return Menu.MAIN
        return None
    elif current_menu == Menu.OBJECT_MANAGEMENT:
        if choice == 1:  # Create Object
            try:
                create_object()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 2:  # List Objects
            try:
                list_objects()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 3:  # Update Object
            try:
                update_object()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 4:  # Delete Object
            try:
                delete_object()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 5:
            return Menu.MAIN
        return None
    elif current_menu == Menu.OBJECTS:
        if choice == 0:
            return Menu.TELESCOPE
        else:
            try:
                # Get objects and allow selection
                objs = list(objects_collection.find({}))
                if 1 <= choice <= len(objs):
                    obj = objs[choice - 1]
                    print(f"Selected: {obj['name']} (RA: {obj.get('ra', 'N/A')}, Dec: {obj.get('dec', 'N/A')})")
                    
                    # Move telescope to object
                    try:
                        # Prefer stored numeric RA/Dec if available; otherwise pass raw strings
                        if 'ra' in obj and 'dec' in obj:
                            ra = obj['ra']
                            dec = obj['dec']
                        else:
                            ra, dec = obj['ra_dec'].split(',')
                            ra = ra.strip()
                            dec = dec.strip()
                        alt, az = C.convert_radec_to_altaz(ra, dec)
                        TM.move_tel(alt, az)
                        print(f"Telescope moved to {obj['name']} (Alt: {alt:.2f}°, Az: {az:.2f}°)")
                        FH.write_log(username, "Object Selection", "success", f"Selected and moved to {obj['name']}")
                    except Exception as e:
                        print(f"Error moving telescope: {e}")
                        FH.write_log(username, "Object Selection", "error", f"Failed to move to {obj['name']}: {e}")
                else:
                    print("Invalid object selection.")
            except Exception as e:
                print(f"Error: {e}")
        return None

# Get validated Alt/Az with input loop
def get_valid_alt_az() -> Tuple[float, float]:
    while True:
        try:
            alt = float(input("Enter Alt (Altitude) degrees (0 to 90): "))
            az = float(input("Enter Az (Azimuth) degrees (25 to 355): "))
            alt_az_input_validation(alt, az)
            return alt, az
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

# Validate alt/az against ranges and config limits
def alt_az_input_validation(alt: float, az: float) -> bool:
    if not isinstance(alt, (float, int)) or not isinstance(az, (float, int)):
        raise ValueError("Alt and Az must be numbers")
    
    # CRITICAL SAFETY CHECK: Prevent negative altitude
    if alt < 0:
        raise ValueError(f"Altitude {alt}° is below horizon! Must be 0° or higher to prevent telescope damage.")
    
    # Use configured limits for validation
    alt_limits = config.get('altitude_limits', [0, 90])
    az_limits = config.get('azimuth_limits', [25, 355])
    if not (alt_limits[0] <= alt <= alt_limits[1]):
        raise ValueError(f"Alt must be between {alt_limits[0]} and {alt_limits[1]} degrees")
    if not (az_limits[0] <= az <= az_limits[1]):
        raise ValueError(f"Az must be between {az_limits[0]} and {az_limits[1]} degrees")
    return True

# Get validated RA/Dec with input loop
def get_valid_ra_dec() -> Tuple[str, str]:
    while True:
        try:
            ra = input("Enter RA (Right Ascension) in hours or HMS format (e.g., 12.5 or 12h30m00s): ")
            dec = input("Enter Dec (Declination) in degrees or DMS format (e.g., 45.5 or +45d30m00s): ")
            ra_dec_input_validation(ra, dec)
            return ra, dec
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def ra_dec_input_validation(ra: str, dec: str) -> bool:
    if not isinstance(ra, str) or not isinstance(dec, str):
        raise ValueError("RA and Dec must be strings")
    if not ra.strip() or not dec.strip():
        raise ValueError("RA and Dec cannot be empty")
    return True

def get_valid_celestial_code() -> str:
    while True:
        try:
            code = input("Enter celestial object code (e.g., M31, NGC1234): ")
            celestial_code_input_validation(code)
            return code
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def celestial_code_input_validation(code: str) -> bool:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Celestial object code must be a non-empty string")
    return True

# Configuration functions
def change_telescope_location():
    print("Current telescope location:")
    print(f"Latitude: {config.get('latitude', 'Not set')}")
    print(f"Longitude: {config.get('longitude', 'Not set')}")
    print(f"Elevation: {config.get('elevation', 'Not set')}")
    
    try:
        lat = float(input("Enter new latitude: "))
        lon = float(input("Enter new longitude: "))
        elev = float(input("Enter new elevation (meters): "))
        
        config.set('latitude', lat)
        config.set('longitude', lon)
        config.set('elevation', elev)
        config.save()
        
        print("Telescope location updated successfully!")
    except ValueError:
        print("Invalid input. Please enter numeric values.")

def change_data_store_location():
    print("Data store location configuration not implemented yet.")

def change_telescope_limits():
    print("Current telescope limits:")
    print(f"Altitude: {config.get('altitude_limits', [0, 90])}")
    print(f"Azimuth: {config.get('azimuth_limits', [25, 355])}")
    
    try:
        alt_min = float(input("Enter minimum altitude: "))
        alt_max = float(input("Enter maximum altitude: "))
        az_min = float(input("Enter minimum azimuth: "))
        az_max = float(input("Enter maximum azimuth: "))
        
        config.set('altitude_limits', [alt_min, alt_max])
        config.set('azimuth_limits', [az_min, az_max])
        config.save()
        
        print("Telescope limits updated successfully!")
    except ValueError:
        print("Invalid input. Please enter numeric values.")

# Display functions
def display_location():
    print("Telescope Location Information:")
    print(f"Latitude: {config.get('latitude', 'Not set')}")
    print(f"Longitude: {config.get('longitude', 'Not set')}")
    print(f"Elevation: {config.get('elevation', 'Not set')}")

def display_all_commands():
    print("\nAll Commands and Descriptions:")
    print("=" * 50)
    for command, description in COMMAND_DESCRIPTIONS.items():
        print(f"{command}: {description}")

def display_available_celestial_objects():
    try:
        ra = input("Enter RA (hours): ")
        dec = input("Enter Dec (degrees): ")
        radius = float(input("Enter search radius (degrees): "))
        
        C.list_available_celestial_objects(ra, dec, radius)
    except ValueError:
        print("Invalid input. Please enter numeric values.")

# Main application loop
def main():
    print("🔭 Welcome to the Telescope Simulator!")
    print("=" * 50)
    
    # Initialize system with default config values
    try:
        required_defaults = {
            'latitude': 0.0,
            'longitude': 0.0,
            'elevation': 0.0,
            'celestial_ping_time': 3,
            'movement_timeout': 10,
            'position_tolerance': 0.01,
            'altitude_limits': [0, 90],
            'azimuth_limits': [25, 355],
            'clamp_to_limits': True,
            'prevent_below_horizon': True,
            'safety_alt_margin_deg': 2.0,
            'safety_az_margin_deg': 1.0,
            'invert_elevation_axis': True,
            'force_first_movement_clockwise': False,
            'tracking_in_background': False,
            'headless_tracking': False,
            'base_joint_name': 'Base_joint',
            'mount_joint_name': 'Mount_joint',
            'base_max_force': 1000.0,
            'elevation_max_force': 1500.0
        }
        
        for key, default_value in required_defaults.items():
            if not config.has(key):
                config.set(key, default_value)
        
        config.save()
        print("✅ System configuration initialized with defaults")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize config defaults: {e}")
    
    # Authenticate user
    user = authenticate()
    if not user:
        print("Authentication failed. Exiting.")
        return
    
    # Main menu loop
    current_menu = Menu.MAIN
    while current_menu is not None:
        try:
            print(f"\n{'='*50}")
            print(f"Current User: {user['username']} ({user.get('role', 'operator')})")
            print(f"Current Menu: {current_menu.name}")
            print('='*50)
            
            # Display menu options
            role = user.get('role', 'operator')
            if current_menu == Menu.MAIN:
                options = MENUS[0][role]
            else:
                options = MENUS[current_menu.value]
            
            for option in options:
                print(option)
            
            # Get user choice
            try:
                choice = int(input("\nEnter your choice: "))
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            
            # Handle menu choice
            next_menu = handle_menu_choice(current_menu, choice, user)
            current_menu = next_menu
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            logging.error(f"Application error: {e}")
    
    print("Thank you for using the Telescope Simulator!")

if __name__ == "__main__":
    main()