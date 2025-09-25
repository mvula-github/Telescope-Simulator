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
    from api.user_api import users_collection, create_user, list_users, update_user, delete_user
    from simulation.track_objects import create_object, list_objects, update_object, delete_object, objects_collection
    from users.middleware.auth import authenticate_user
    
    print("✅ Successfully imported from new package structure!")
    
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("🔄 Falling back to old imports...")
    
    # Fallback to old imports (in case migration isn't complete)
    import core.file_handling as FH
    import core.telescope_control as TM
    import core.calculations as C
    import core.system_checks as SCh
    from core.system_config import config
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
    2: ["1. Change Telescope Location", "2. Change Telescope Limits", "3. Change Movement Settings", "4. Change Safety Settings", "5. Change Simulation Settings", "6. View All Settings", "7. Back"],
    3: ["1. Convert Alt & Az to Ra & Dec", "2. Convert Ra & Dec to Alt & Az", "3. Back"],
    4: ["1. Create User", "2. List Users", "3. Update User", "4. Delete User", "5. Back"],
    5: ["1. Display Location", "2. Display Telescope Logs", "3. Display All Commands & Descriptions", 
        "4. Display Available Celestial Objects", "5. Check Internet Connection", "6. Back"],
    6: ["1. Create Object", "2. List Objects", "3. Update Object", "4. Delete Object", "5. Back"],
    7: ["Select a celestial object to track (will show all available objects)"]
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
                TM.move_tel(alt, az, username)
                print(f"Telescope moved to Alt: {alt}, Az: {az}")
                FH.write_log(username, "Point to AltAz", "success", f"Moved telescope to Alt: {alt}, Az: {az}", username)
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Point to AltAz", "error", str(e), username)
        elif choice == 2:  # Point to RaDec
            try:
                ra, dec = get_valid_ra_dec()
                alt, az = C.convert_radec_to_altaz(ra, dec)
                TM.move_tel(alt, az, username)
                print(f"Telescope moved to RA: {ra}, Dec: {dec} (Alt: {alt}, Az: {az})")
                FH.write_log(username, "Point to RaDec", "success", f"Moved telescope to RA: {ra}, Dec: {dec}", username)
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Point to RaDec", "error", str(e), username)
        elif choice == 3:  # Tracking
            try:
                code = get_valid_celestial_code()
                TM.track_celestial_object(code, username)
                FH.write_log(username, "Tracking", "success", f"Started tracking celestial object: {code}", username)
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Tracking", "error", str(e), username)
        elif choice == 4:  # Rest Mode
            try:
                TM.telescope_rest(username, username)
                print("Telescope moved to rest position.")
                FH.write_log(username, "Rest Mode", "success", "Telescope moved to rest position", username)
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Rest Mode", "error", str(e), username)
        elif choice == 5:  # Objects submenu
            return Menu.OBJECTS
        elif choice == 6:
            return Menu.MAIN
        return Menu.TELESCOPE  # Stay in telescope menu instead of returning None
    elif current_menu == Menu.CONFIG:
        if choice == 1:  # Change Telescope Location
            try:
                change_telescope_location()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 2:  # Change Telescope Limits
            try:
                change_telescope_limits()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 3:  # Change Movement Settings
            try:
                change_movement_settings()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 4:  # Change Safety Settings
            try:
                change_safety_settings()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 5:  # Change Simulation Settings
            try:
                change_simulation_settings()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 6:  # View All Settings
            try:
                view_all_settings()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 7:
            return Menu.MAIN
        return Menu.CONFIG  # Stay in config menu
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
        return Menu.COORDS  # Stay in coords menu
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
        return Menu.USER_MANAGEMENT  # Stay in user management menu
    elif current_menu == Menu.DISPLAY:
        if choice == 1:  # Display Location
            try:
                display_location()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 2:  # Display Telescope Logs
            try:
                display_telescope_logs()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 3:  # Display All Commands & Descriptions
            try:
                display_all_commands()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 4:  # Display Available Celestial Objects
            try:
                display_objects()
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 5:  # Check Internet Connection
            try:
                status = SCh.check_internet_connection()
                print(f"Internet Connection: {status.message}")
            except Exception as e:
                print(f"Error: {e}")
        elif choice == 6:
            return Menu.MAIN
        return Menu.DISPLAY  # Stay in display menu
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
        return Menu.OBJECT_MANAGEMENT  # Stay in object management menu
    elif current_menu == Menu.OBJECTS:
        if choice == 0:
            return Menu.TELESCOPE
        else:
            try:
                # Get objects and display them first
                from simulation.track_objects import list_objects as list_objects_func
                objs = list_objects_func(show_all=True)
                if not objs:
                    print("No celestial objects available.")
                    print("Please add objects through Object Management first.")
                    return Menu.OBJECTS
                
                # Display all available objects
                print("\n" + "="*60)
                print("AVAILABLE CELESTIAL OBJECTS")
                print("="*60)
                for i, obj in enumerate(objs, 1):
                    print(f"{i:2d}. {obj['name']}")
                    print(f"    Description: {obj.get('description', 'No description')}")
                    if 'ra' in obj and 'dec' in obj:
                        print(f"    Coordinates: RA: {obj['ra']}, Dec: {obj['dec']}")
                    elif 'ra_dec' in obj:
                        print(f"    Coordinates: {obj['ra_dec']}")
                    print(f"    NED Code: {obj.get('ned_code', 'N/A')}")
                    print()
                
                print("="*60)
                print("Enter the number of the object you want to track (0 to go back):")
                
                # Get user selection
                try:
                    selection = int(input("Your choice: "))
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    return Menu.OBJECTS
                
                if selection == 0:
                    return Menu.TELESCOPE
                elif 1 <= selection <= len(objs):
                    obj = objs[selection - 1]
                    print(f"\nSelected: {obj['name']}")
                    
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
                        print(f"Converting coordinates: RA: {ra}, Dec: {dec} -> Alt: {alt:.2f}°, Az: {az:.2f}°")
                        TM.move_tel(alt, az, username)
                        print(f"Telescope moved to {obj['name']} (Alt: {alt:.2f}°, Az: {az:.2f}°)")
                        FH.write_log(username, "Object Selection", "success", f"Selected and moved to {obj['name']}", username)
                    except Exception as e:
                        print(f"Error moving telescope: {e}")
                        FH.write_log(username, "Object Selection", "error", f"Failed to move to {obj['name']}: {e}", username)
                else:
                    print("Invalid object selection.")
            except Exception as e:
                print(f"Error: {e}")
        return Menu.OBJECTS  # Stay in objects menu

# Get validated Alt/Az with input loop
def get_valid_alt_az() -> Tuple[float, float]:
    while True:
        try:
            alt = float(input("Enter Alt (Altitude) degrees (5 to 90): "))
            az = float(input("Enter Az (Azimuth) degrees (25 to 335): "))
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
    alt_limits = config.get('altitude_limits', [5, 90])
    az_limits = config.get('azimuth_limits', [25, 335])
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
    """Change telescope location settings with validation."""
    print("\n=== CHANGE TELESCOPE LOCATION ===")
    print("Current telescope location:")
    print(f"  Latitude: {config.get('latitude', 'Not set')}°")
    print(f"  Longitude: {config.get('longitude', 'Not set')}°")
    print(f"  Elevation: {config.get('elevation', 'Not set')} meters")
    
    try:
        print("\nEnter new location values:")
        lat = float(input("Enter latitude (-90 to 90): "))
        if not -90 <= lat <= 90:
            print("Error: Latitude must be between -90 and 90 degrees.")
            return
            
        lon = float(input("Enter longitude (-180 to 180): "))
        if not -180 <= lon <= 180:
            print("Error: Longitude must be between -180 and 180 degrees.")
            return
            
        elev = float(input("Enter elevation in meters: "))
        if elev < 0:
            print("Error: Elevation cannot be negative.")
            return
        
        # Confirm changes
        print(f"\nNew location will be:")
        print(f"  Latitude: {lat}°")
        print(f"  Longitude: {lon}°")
        print(f"  Elevation: {elev} meters")
        
        confirm = input("\nSave these changes? (yes/no): ").strip().lower()
        if confirm == 'yes':
            config.set('latitude', lat)
            config.set('longitude', lon)
            config.set('elevation', elev)
            config.save()
            print("✅ Telescope location updated successfully!")
            FH.write_log("admin", "Change Location", "success", f"Updated location to Lat: {lat}, Lon: {lon}, Elev: {elev}", "admin")
        else:
            print("Changes cancelled.")
        
    except ValueError:
        print("❌ Invalid input. Please enter numeric values.")
        FH.write_log("admin", "Change Location", "error", "Invalid input provided", "admin")
    except Exception as e:
        print(f"❌ Error updating location: {e}")
        FH.write_log("admin", "Change Location", "error", str(e), "admin")

def change_movement_settings():
    """Change telescope movement settings."""
    print("\n=== CHANGE MOVEMENT SETTINGS ===")
    print("Current movement settings:")
    print(f"  Movement Timeout: {config.get('movement_timeout', 10)} seconds")
    print(f"  Position Tolerance: {config.get('position_tolerance', 0.01)} degrees")
    print(f"  Clamp to Limits: {config.get('clamp_to_limits', True)}")
    print(f"  Invert Elevation Axis: {config.get('invert_elevation_axis', True)}")
    print(f"  Force First Movement Clockwise: {config.get('force_first_movement_clockwise', False)}")
    
    try:
        print("\nEnter new movement settings:")
        
        timeout = float(input("Enter movement timeout in seconds (1-60): "))
        if not 1 <= timeout <= 60:
            print("Error: Timeout must be between 1 and 60 seconds.")
            return
            
        tolerance = float(input("Enter position tolerance in degrees (0.001-1.0): "))
        if not 0.001 <= tolerance <= 1.0:
            print("Error: Tolerance must be between 0.001 and 1.0 degrees.")
            return
            
        clamp_input = input("Clamp to limits? (yes/no): ").strip().lower()
        clamp_to_limits = clamp_input == 'yes'
        
        invert_input = input("Invert elevation axis? (yes/no): ").strip().lower()
        invert_elevation = invert_input == 'yes'
        
        clockwise_input = input("Force first movement clockwise? (yes/no): ").strip().lower()
        force_clockwise = clockwise_input == 'yes'
        
        # Confirm changes
        print(f"\nNew movement settings will be:")
        print(f"  Movement Timeout: {timeout} seconds")
        print(f"  Position Tolerance: {tolerance} degrees")
        print(f"  Clamp to Limits: {clamp_to_limits}")
        print(f"  Invert Elevation Axis: {invert_elevation}")
        print(f"  Force First Movement Clockwise: {force_clockwise}")
        
        confirm = input("\nSave these changes? (yes/no): ").strip().lower()
        if confirm == 'yes':
            config.set('movement_timeout', timeout)
            config.set('position_tolerance', tolerance)
            config.set('clamp_to_limits', clamp_to_limits)
            config.set('invert_elevation_axis', invert_elevation)
            config.set('force_first_movement_clockwise', force_clockwise)
            config.save()
            print("✅ Movement settings updated successfully!")
            FH.write_log("admin", "Change Movement Settings", "success", f"Updated movement settings", "admin")
        else:
            print("Changes cancelled.")
            
    except ValueError:
        print("❌ Invalid input. Please enter numeric values.")
        FH.write_log("admin", "Change Movement Settings", "error", "Invalid input provided", "admin")
    except Exception as e:
        print(f"❌ Error updating movement settings: {e}")
        FH.write_log("admin", "Change Movement Settings", "error", str(e), "admin")

def change_safety_settings():
    """Change telescope safety settings."""
    print("\n=== CHANGE SAFETY SETTINGS ===")
    print("Current safety settings:")
    print(f"  Prevent Below Horizon: {config.get('prevent_below_horizon', True)}")
    print(f"  Safety Altitude Margin: {config.get('safety_alt_margin_deg', 0.5)}°")
    print(f"  Safety Azimuth Margin: {config.get('safety_az_margin_deg', 1.0)}°")
    
    try:
        print("\nEnter new safety settings:")
        
        prevent_input = input("Prevent below horizon? (yes/no): ").strip().lower()
        prevent_below = prevent_input == 'yes'
        
        alt_margin = float(input("Enter safety altitude margin in degrees (0.1-5.0): "))
        if not 0.1 <= alt_margin <= 5.0:
            print("Error: Altitude margin must be between 0.1 and 5.0 degrees.")
            return
            
        az_margin = float(input("Enter safety azimuth margin in degrees (0.1-10.0): "))
        if not 0.1 <= az_margin <= 10.0:
            print("Error: Azimuth margin must be between 0.1 and 10.0 degrees.")
            return
        
        # Confirm changes
        print(f"\nNew safety settings will be:")
        print(f"  Prevent Below Horizon: {prevent_below}")
        print(f"  Safety Altitude Margin: {alt_margin}°")
        print(f"  Safety Azimuth Margin: {az_margin}°")
        
        confirm = input("\nSave these changes? (yes/no): ").strip().lower()
        if confirm == 'yes':
            config.set('prevent_below_horizon', prevent_below)
            config.set('safety_alt_margin_deg', alt_margin)
            config.set('safety_az_margin_deg', az_margin)
            config.save()
            print("✅ Safety settings updated successfully!")
            FH.write_log("admin", "Change Safety Settings", "success", f"Updated safety settings", "admin")
        else:
            print("Changes cancelled.")
            
    except ValueError:
        print("❌ Invalid input. Please enter numeric values.")
        FH.write_log("admin", "Change Safety Settings", "error", "Invalid input provided", "admin")
    except Exception as e:
        print(f"❌ Error updating safety settings: {e}")
        FH.write_log("admin", "Change Safety Settings", "error", str(e), "admin")

def change_simulation_settings():
    """Change simulation and joint settings."""
    print("\n=== CHANGE SIMULATION SETTINGS ===")
    print("Current simulation settings:")
    print(f"  Base Joint Name: {config.get('base_joint_name', 'Base_joint')}")
    print(f"  Mount Joint Name: {config.get('mount_joint_name', 'Mount_joint')}")
    print(f"  Base Max Force: {config.get('base_max_force', 1000.0)} N")
    print(f"  Elevation Max Force: {config.get('elevation_max_force', 1500.0)} N")
    print(f"  Celestial Ping Time: {config.get('celestial_ping_time', 3)} seconds")
    print(f"  Tracking in Background: {config.get('tracking_in_background', False)}")
    print(f"  Headless Tracking: {config.get('headless_tracking', False)}")
    
    try:
        print("\nEnter new simulation settings:")
        
        base_joint = input("Enter base joint name: ").strip()
        if not base_joint:
            print("Error: Base joint name cannot be empty.")
            return
            
        mount_joint = input("Enter mount joint name: ").strip()
        if not mount_joint:
            print("Error: Mount joint name cannot be empty.")
            return
            
        base_force = float(input("Enter base max force in N (100-5000): "))
        if not 100 <= base_force <= 5000:
            print("Error: Base force must be between 100 and 5000 N.")
            return
            
        elevation_force = float(input("Enter elevation max force in N (100-5000): "))
        if not 100 <= elevation_force <= 5000:
            print("Error: Elevation force must be between 100 and 5000 N.")
            return
            
        ping_time = float(input("Enter celestial ping time in seconds (1-30): "))
        if not 1 <= ping_time <= 30:
            print("Error: Ping time must be between 1 and 30 seconds.")
            return
            
        background_input = input("Enable tracking in background? (yes/no): ").strip().lower()
        tracking_background = background_input == 'yes'
        
        headless_input = input("Enable headless tracking? (yes/no): ").strip().lower()
        headless_tracking = headless_input == 'yes'
        
        # Confirm changes
        print(f"\nNew simulation settings will be:")
        print(f"  Base Joint Name: {base_joint}")
        print(f"  Mount Joint Name: {mount_joint}")
        print(f"  Base Max Force: {base_force} N")
        print(f"  Elevation Max Force: {elevation_force} N")
        print(f"  Celestial Ping Time: {ping_time} seconds")
        print(f"  Tracking in Background: {tracking_background}")
        print(f"  Headless Tracking: {headless_tracking}")
        
        confirm = input("\nSave these changes? (yes/no): ").strip().lower()
        if confirm == 'yes':
            config.set('base_joint_name', base_joint)
            config.set('mount_joint_name', mount_joint)
            config.set('base_max_force', base_force)
            config.set('elevation_max_force', elevation_force)
            config.set('celestial_ping_time', ping_time)
            config.set('tracking_in_background', tracking_background)
            config.set('headless_tracking', headless_tracking)
            config.save()
            print("✅ Simulation settings updated successfully!")
            FH.write_log("admin", "Change Simulation Settings", "success", f"Updated simulation settings", "admin")
        else:
            print("Changes cancelled.")
            
    except ValueError:
        print("❌ Invalid input. Please enter numeric values.")
        FH.write_log("admin", "Change Simulation Settings", "error", "Invalid input provided", "admin")
    except Exception as e:
        print(f"❌ Error updating simulation settings: {e}")
        FH.write_log("admin", "Change Simulation Settings", "error", str(e), "admin")

def view_all_settings():
    """Display all current configuration settings."""
    print("\n=== ALL CONFIGURATION SETTINGS ===")
    print("=" * 50)
    
    # Location settings
    print("📍 LOCATION SETTINGS:")
    print(f"  Latitude: {config.get('latitude', 'Not set')}°")
    print(f"  Longitude: {config.get('longitude', 'Not set')}°")
    print(f"  Elevation: {config.get('elevation', 'Not set')} meters")
    
    # Movement limits
    print("\n🎯 MOVEMENT LIMITS:")
    alt_limits = config.get('altitude_limits', [5, 90])
    az_limits = config.get('azimuth_limits', [25, 335])
    print(f"  Altitude: {alt_limits[0]}° to {alt_limits[1]}°")
    print(f"  Azimuth: {az_limits[0]}° to {az_limits[1]}°")
    
    # Movement settings
    print("\n⚙️ MOVEMENT SETTINGS:")
    print(f"  Movement Timeout: {config.get('movement_timeout', 10)} seconds")
    print(f"  Position Tolerance: {config.get('position_tolerance', 0.01)} degrees")
    print(f"  Clamp to Limits: {config.get('clamp_to_limits', True)}")
    print(f"  Invert Elevation Axis: {config.get('invert_elevation_axis', True)}")
    print(f"  Force First Movement Clockwise: {config.get('force_first_movement_clockwise', False)}")
    
    # Safety settings
    print("\n🛡️ SAFETY SETTINGS:")
    print(f"  Prevent Below Horizon: {config.get('prevent_below_horizon', True)}")
    print(f"  Safety Altitude Margin: {config.get('safety_alt_margin_deg', 0.5)}°")
    print(f"  Safety Azimuth Margin: {config.get('safety_az_margin_deg', 1.0)}°")
    
    # Simulation settings
    print("\n🎮 SIMULATION SETTINGS:")
    print(f"  Base Joint Name: {config.get('base_joint_name', 'Base_joint')}")
    print(f"  Mount Joint Name: {config.get('mount_joint_name', 'Mount_joint')}")
    print(f"  Base Max Force: {config.get('base_max_force', 1000.0)} N")
    print(f"  Elevation Max Force: {config.get('elevation_max_force', 1500.0)} N")
    print(f"  Celestial Ping Time: {config.get('celestial_ping_time', 3)} seconds")
    print(f"  Tracking in Background: {config.get('tracking_in_background', False)}")
    print(f"  Headless Tracking: {config.get('headless_tracking', False)}")
    
    print("\n" + "=" * 50)
    FH.write_log("admin", "View All Settings", "success", "Viewed all configuration settings", "admin")

def change_telescope_limits():
    """Change telescope movement limits with validation."""
    print("\n=== CHANGE TELESCOPE LIMITS ===")
    print("Current telescope limits:")
    alt_limits = config.get('altitude_limits', [5, 90])
    az_limits = config.get('azimuth_limits', [25, 335])
    print(f"  Altitude: {alt_limits[0]}° to {alt_limits[1]}°")
    print(f"  Azimuth: {az_limits[0]}° to {az_limits[1]}°")
    
    try:
        print("\nEnter new limit values:")
        alt_min = float(input("Enter minimum altitude (0-90): "))
        alt_max = float(input("Enter maximum altitude (0-90): "))
        az_min = float(input("Enter minimum azimuth (0-360): "))
        az_max = float(input("Enter maximum azimuth (0-360): "))
        
        # Validate altitude limits
        if not 0 <= alt_min <= 90:
            print("Error: Minimum altitude must be between 0 and 90 degrees.")
            return
        if not 0 <= alt_max <= 90:
            print("Error: Maximum altitude must be between 0 and 90 degrees.")
            return
        if alt_min >= alt_max:
            print("Error: Minimum altitude must be less than maximum altitude.")
            return
            
        # Validate azimuth limits
        if not 0 <= az_min <= 360:
            print("Error: Minimum azimuth must be between 0 and 360 degrees.")
            return
        if not 0 <= az_max <= 360:
            print("Error: Maximum azimuth must be between 0 and 360 degrees.")
            return
        if az_min >= az_max:
            print("Error: Minimum azimuth must be less than maximum azimuth.")
            return
        
        # Confirm changes
        print(f"\nNew limits will be:")
        print(f"  Altitude: {alt_min}° to {alt_max}°")
        print(f"  Azimuth: {az_min}° to {az_max}°")
        
        confirm = input("\nSave these changes? (yes/no): ").strip().lower()
        if confirm == 'yes':
            config.set('altitude_limits', [alt_min, alt_max])
            config.set('azimuth_limits', [az_min, az_max])
            config.save()
            print("✅ Telescope limits updated successfully!")
            FH.write_log("admin", "Change Limits", "success", f"Updated limits: Alt {alt_min}-{alt_max}°, Az {az_min}-{az_max}°", "admin")
        else:
            print("Changes cancelled.")
        
    except ValueError:
        print("❌ Invalid input. Please enter numeric values.")
        FH.write_log("admin", "Change Limits", "error", "Invalid input provided", "admin")
    except Exception as e:
        print(f"❌ Error updating limits: {e}")
        FH.write_log("admin", "Change Limits", "error", str(e), "admin")

# Display functions
def display_location():
    print("Telescope Location Information:")
    print(f"Latitude: {config.get('latitude', 'Not set')}")
    print(f"Longitude: {config.get('longitude', 'Not set')}")
    print(f"Elevation: {config.get('elevation', 'Not set')}")

def display_limits():
    """Display current telescope limits."""
    try:
        alt_limits = config.get('altitude_limits', [5, 90])
        az_limits = config.get('azimuth_limits', [25, 335])
        print(f"Current telescope limits:")
        print(f"  Altitude: {alt_limits[0]}° to {alt_limits[1]}°")
        print(f"  Azimuth: {az_limits[0]}° to {az_limits[1]}°")
    except Exception as e:
        print(f"Error displaying limits: {e}")

def display_objects():
    """Display all celestial objects."""
    try:
        objects = list_objects(show_all=True)
        if objects:
            print("Available celestial objects:")
            for i, obj in enumerate(objects, 1):
                print(f"  {i}. {obj['name']} - {obj.get('description', 'No description')}")
        else:
            print("No celestial objects found.")
    except Exception as e:
        print(f"Error displaying objects: {e}")

def display_users():
    """Display all users."""
    try:
        users = list_users()
        if users:
            print("Available users:")
            for user in users:
                print(f"  Username: {user['username']}, Role: {user.get('role', 'operator')}, Name: {user.get('name', 'N/A')}")
        else:
            print("No users found.")
    except Exception as e:
        print(f"Error displaying users: {e}")

def display_telescope_logs():
    """Display recent telescope logs."""
    try:
        log_file = "logs/telescope.log"
        if os.path.exists(log_file):
            print("Recent telescope logs:")
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Show last 10 lines
                for line in lines[-10:]:
                    print(f"  {line.strip()}")
        else:
            print("No telescope logs found.")
    except Exception as e:
        print(f"Error displaying logs: {e}")

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

# Object Management Wrapper Functions
def create_object():
    """Wrapper function to create a new celestial object with user input."""
    try:
        print("\n=== CREATE CELESTIAL OBJECT ===")
        name = input("Enter object name: ").strip()
        if not name:
            print("Error: Object name cannot be empty.")
            return
        
        description = input("Enter object description: ").strip()
        if not description:
            print("Error: Object description cannot be empty.")
            return
        
        ra_dec = input("Enter RA/Dec coordinates (format: RA,Dec): ").strip()
        if not ra_dec:
            print("Error: RA/Dec coordinates cannot be empty.")
            return
        
        ned_code = input("Enter NED code: ").strip()
        if not ned_code:
            print("Error: NED code cannot be empty.")
            return
        
        # For now, use a default user_id for admin users
        # In a real system, this would come from the authenticated user
        user_id = "admin"
        
        # Call the actual create_object function
        from simulation.track_objects import create_object as create_obj_func
        create_obj_func(user_id, name, description, ra_dec, ned_code)
        
        # Log the action
        FH.write_log("admin", "Create Object", "success", f"Created object: {name}", "admin")
        
    except Exception as e:
        print(f"Error creating object: {e}")
        FH.write_log("admin", "Create Object", "error", str(e), "admin")

def list_objects():
    """Wrapper function to list celestial objects."""
    try:
        print("\n=== LIST CELESTIAL OBJECTS ===")
        # Use show_all=True to display all objects for admin
        from simulation.track_objects import list_objects as list_objects_func
        objects = list_objects_func(show_all=True)
        if not objects:
            print("No celestial objects found.")
        FH.write_log("admin", "List Objects", "success", "Listed all objects", "admin")
    except Exception as e:
        print(f"Error listing objects: {e}")
        FH.write_log("admin", "List Objects", "error", str(e), "admin")

def update_object():
    """Wrapper function to update a celestial object with user input."""
    try:
        print("\n=== UPDATE CELESTIAL OBJECT ===")
        
        # First, show available objects
        print("Available objects:")
        from simulation.track_objects import list_objects as list_objects_func
        objects = list_objects_func(show_all=True)
        if not objects:
            print("No objects available to update.")
            return
        
        name = input("\nEnter the name of the object to update: ").strip()
        if not name:
            print("Error: Object name cannot be empty.")
            return
        
        print(f"\nUpdating object: {name}")
        print("Leave fields empty to keep current values.")
        
        description = input("Enter new description (or press Enter to keep current): ").strip()
        ra_dec = input("Enter new RA/Dec coordinates (format: RA,Dec) (or press Enter to keep current): ").strip()
        ned_code = input("Enter new NED code (or press Enter to keep current): ").strip()
        
        # Convert empty strings to None for optional parameters
        description = description if description else None
        ra_dec = ra_dec if ra_dec else None
        ned_code = ned_code if ned_code else None
        
        # For now, use a default user_id for admin users
        user_id = "admin"
        role = "admin"
        
        # Call the actual update_object function
        from simulation.track_objects import update_object as update_obj_func
        update_obj_func(name, description, ra_dec, ned_code, user_id, role)
        
        # Log the action
        FH.write_log("admin", "Update Object", "success", f"Updated object: {name}", "admin")
        
    except Exception as e:
        print(f"Error updating object: {e}")
        FH.write_log("admin", "Update Object", "error", str(e), "admin")

def delete_object():
    """Wrapper function to delete a celestial object with user input."""
    try:
        print("\n=== DELETE CELESTIAL OBJECT ===")
        
        # First, show available objects
        print("Available objects:")
        from simulation.track_objects import list_objects as list_objects_func
        objects = list_objects_func(show_all=True)
        if not objects:
            print("No objects available to delete.")
            return
        
        name = input("\nEnter the name of the object to delete: ").strip()
        if not name:
            print("Error: Object name cannot be empty.")
            return
        
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete '{name}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Deletion cancelled.")
            return
        
        # For now, use a default user_id for admin users
        user_id = "admin"
        role = "admin"
        
        # Call the actual delete_object function
        from simulation.track_objects import delete_object as delete_obj_func
        delete_obj_func(name, user_id, role)
        
        # Log the action
        FH.write_log("admin", "Delete Object", "success", f"Deleted object: {name}", "admin")
        
    except Exception as e:
        print(f"Error deleting object: {e}")
        FH.write_log("admin", "Delete Object", "error", str(e), "admin")

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
    
    # Close telescope connection when exiting
    try:
        TM.close()
    except Exception as e:
        print(f"Warning: Error closing telescope connection: {e}")
    
    print("Thank you for using the Telescope Simulator!")

if __name__ == "__main__":
    main()