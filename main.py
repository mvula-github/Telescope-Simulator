import getpass
import logging
import time
from enum import Enum
from typing import Optional, Tuple
import re
from dotenv import load_dotenv
import os
from datetime import datetime
import File_Handling as FH
import Telescope_Movement as TM
import Calculations as C
import System_Checks as SCh
from System_Config import config
from werkzeug.security import generate_password_hash
from users.middleware.auth import authenticate_user
from user_management import create_user, list_users, update_user, delete_user, users_collection
from Track_Objects import create_object, list_objects, update_object, delete_object, objects_collection

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
    max_attempts = 3
    attempts = 0
    backoff_seconds = 1
    while attempts < max_attempts:
        try:
            username = input("Enter username: ")
            password = getpass.getpass("Enter password: ")
            def getUsername(u):
                user = users_collection.find_one({"username": u})
                if user:
                    # Use 'password' field directly
                    pw_hash = user.get('password')
                    if not pw_hash:
                        return None
                    # Keep pw_hash as string for Werkzeug
                    return {
                        'id': str(user['_id']),
                        'password': pw_hash  # Use 'password' field
                    }
                return None
            token, error = authenticate_user(username, password, getUsername)
            if error:
                attempts += 1
                remaining = max_attempts - attempts
                FH.write_log(username, "Login", "error", f"Failed login attempt: {error}. {remaining} attempts remaining.")
                print(f"Incorrect credentials: {error}. {remaining} attempts remaining.")
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 8)
            else:
                user = users_collection.find_one({"username": username})
                FH.write_log(username, "Login", "success", f"Login successful as {user['role']}")
                print(f"Access granted as {user['role']}.\n")
                return user
        except Exception as e:
            logging.error(f"Failed to authenticate: {e}")
            return None
    print("Maximum login attempts reached. Exiting.")
    exit(1)

# Display menu based on user role and menu ID
def display_menu(menu_id: int, role: str):
    options = MENUS.get(menu_id)
    if options is None:
        print("Menu not found.")
        return
    if isinstance(options, dict):
        options = options.get(role, options.get('admin', []))
    for option in options:
        print(option)
    print("Enter your choice (number):")

# Get and validate menu choice
def get_menu_choice() -> int:
    while True:
        try:
            choice = int(input("> "))
            return choice
        except ValueError:
            print("Please enter a valid number.")

# Handle menu choices and return the next menu or None to stay in current
def handle_menu_choice(current_menu: Menu, choice: int, user: dict) -> Optional[Menu]:
    username = user['username']
    role = user['role']
    # Handle "Back" option for each submenu
    if current_menu == Menu.TELESCOPE and choice == 6:
        return Menu.MAIN
    if current_menu == Menu.CONFIG and choice == 4:
        return Menu.MAIN
    if current_menu == Menu.COORDS and choice == 3:
        return Menu.MAIN
    if current_menu == Menu.USER_MANAGEMENT and choice == 5:
        return Menu.MAIN
    if current_menu == Menu.DISPLAY and choice == 6:
        return Menu.MAIN
    if current_menu == Menu.OBJECTS and choice == 0:
        return Menu.TELESCOPE
    if current_menu == Menu.OBJECT_MANAGEMENT and choice == 5:
        return Menu.MAIN

    if current_menu == Menu.MAIN:
        if choice == 1:
            return Menu.TELESCOPE
        elif choice == 2 and role == 'admin':
            return Menu.CONFIG
        elif choice == 3 and role == 'admin':
            return Menu.COORDS
        elif choice == 4 and role == 'admin':
            return Menu.USER_MANAGEMENT
        elif choice == 5:
            return Menu.DISPLAY
        elif choice == 6 and role == 'admin':
            return Menu.OBJECT_MANAGEMENT
        elif (role == 'admin' and choice == 7) or (role == 'operator' and choice == 3):
            return None  # Exit
        else:
            print("Invalid choice or insufficient permissions.")
            FH.write_log(username, f"Main Menu Choice {choice}", "error", "Invalid choice or insufficient permissions")
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
    elif current_menu == Menu.OBJECTS:
        # List objects from the database
        if objects_collection is None:
            print("Database not initialized.")
            return Menu.TELESCOPE
        try:
            # Admins see all; operators see only their own
            query = {} if role == 'admin' else {'user_id': str(user['_id'])}
            objs = list(objects_collection.find(query))
            if not objs:
                print("No astronomical objects found.")
                return Menu.TELESCOPE
            print("\nAvailable Objects:")
            for idx, obj in enumerate(objs, 1):
                print(f"{idx}. {obj['name']} - {obj['description']}")
            print("0. Back")
            selection = input("Select an object by number (or 0 to go back): ")
            if not selection.isdigit():
                print("Invalid input.")
                return Menu.OBJECTS
            selection = int(selection)
            if selection == 0:
                return Menu.TELESCOPE
            if 1 <= selection <= len(objs):
                obj = objs[selection - 1]
                # Display selected object details before moving telescope
                print(f"\nSelected: {obj['name']}")
                print(f"Description: {obj['description']}")
                print(f"RA/Dec: {obj['ra_dec']}")
                print(f"NED Code: {obj['ned_code']}")
                try:
                    # Prefer stored numeric RA/Dec if available
                    if 'ra' in obj and 'dec' in obj:
                        ra = float(obj['ra'])
                        dec = float(obj['dec'])
                    else:
                        ra_str, dec_str = obj['ra_dec'].split(',')
                        ra = float(ra_str.strip())
                        dec = float(dec_str.strip())
                    alt, az = C.convert_radec_to_altaz(ra, dec)
                    TM.move_tel(alt, az)
                    print(f"Telescope pointed to {obj['name']} (RA: {ra}, Dec: {dec})")
                    FH.write_log(username, f"Point to {obj['name']}", "success", f"Moved telescope to {obj['name']} (RA: {ra}, Dec: {dec})")
                except Exception as e:
                    print(f"Error: {e}")
                    FH.write_log(username, f"Point to {obj['name']}", "error", str(e))
                return Menu.OBJECTS
            else:
                print("Invalid selection.")
                return Menu.OBJECTS
        except Exception as e:
            logging.error(f"Objects menu error: {e}")
            return Menu.TELESCOPE
    elif current_menu == Menu.CONFIG and role == 'admin':
        if choice == 1:
            # Change Telescope Location
            try:
                lat = float(input("Enter new Latitude: "))
                lon = float(input("Enter new Longitude: "))
                ele = float(input("Enter new Elevation (meters): "))
                config.update('latitude', lat)
                config.update('longitude', lon)
                config.update('elevation', ele)
                print("Telescope location updated.")
                FH.write_log(username, "Configure Location", "success", f"Set lat={lat}, lon={lon}, ele={ele}")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Configure Location", "error", str(e))
        elif choice == 2:
            # Change Data Store Location
            try:
                path = input("Enter new data store directory path: ")
                config.update('data_store_location', path)
                print("Data store location updated.")
                FH.write_log(username, "Configure Data Store", "success", path)
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Configure Data Store", "error", str(e))
        elif choice == 3:
            # Change Telescope Limits
            try:
                alt_min = float(input("Enter Altitude Min (-90..90): "))
                alt_max = float(input("Enter Altitude Max (-90..90): "))
                az_min = float(input("Enter Azimuth Min (0..360): "))
                az_max = float(input("Enter Azimuth Max (0..360): "))
                config.update('altitude_limits', [alt_min, alt_max])
                config.update('azimuth_limits', [az_min, az_max])
                print("Telescope limits updated.")
                FH.write_log(username, "Configure Limits", "success", f"Alt:[{alt_min},{alt_max}] Az:[{az_min},{az_max}]")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Configure Limits", "error", str(e))
        elif choice == 4:
            return Menu.MAIN
        else:
            print("Invalid choice.")
        return None
    elif current_menu == Menu.COORDS and role == 'admin':
        if choice == 1:
            # Convert Alt/Az to RA/Dec
            try:
                alt, az = get_valid_alt_az()
                ra, dec = C.convert_altaz_to_radec(alt, az)
                print(f"Converted Alt/Az ({alt}, {az}) -> RA: {ra:.3f}h, Dec: {dec:.3f}°")
                FH.write_log(username, "Convert AltAz->RaDec", "success", f"Alt:{alt},Az:{az} -> RA:{ra},Dec:{dec}")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Convert AltAz->RaDec", "error", str(e))
        elif choice == 2:
            # Convert RA/Dec to Alt/Az
            try:
                ra, dec = get_valid_ra_dec()
                alt, az = C.convert_radec_to_altaz(ra, dec)
                print(f"Converted RA/Dec ({ra}, {dec}) -> Alt: {alt:.2f}°, Az: {az:.2f}°")
                FH.write_log(username, "Convert RaDec->AltAz", "success", f"RA:{ra},Dec:{dec} -> Alt:{alt},Az:{az}")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Convert RaDec->AltAz", "error", str(e))
        elif choice == 3:
            return Menu.MAIN
        else:
            print("Invalid choice.")
        return None
    elif current_menu == Menu.DISPLAY:
        if choice == 1:
            # Display Location
            try:
                lat, lon, ele = C.get_location_and_elevation('stored')
                print(f"Stored Location -> Latitude: {lat}, Longitude: {lon}, Elevation: {ele}m")
                FH.write_log(username, "Display Location", "success", f"lat={lat}, lon={lon}, ele={ele}")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Display Location", "error", str(e))
        elif choice == 2:
            # Display Telescope Logs
            try:
                FH.display_logs()
                FH.write_log(username, "Display Logs", "success", "Displayed logs")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Display Logs", "error", str(e))
        elif choice == 3:
            # Display All Commands & Descriptions
            try:
                for cmd, desc in COMMAND_DESCRIPTIONS.items():
                    print(f"- {cmd}: {desc}")
                FH.write_log(username, "Display Commands", "success", "Displayed commands")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Display Commands", "error", str(e))
        elif choice == 4:
            # Display Available Celestial Objects
            try:
                ra, dec = get_valid_ra_dec()
                radius_str = input("Enter search radius in degrees (default 0.1): ").strip()
                radius = float(radius_str) if radius_str else 0.1
                C.list_available_celestial_objects(ra, dec, radius)
                FH.write_log(username, "Display Objects", "success", f"Around RA:{ra},Dec:{dec},R:{radius}")
            except Exception as e:
                print(f"Error: {e}")
                FH.write_log(username, "Display Objects", "error", str(e))
        elif choice == 5:
            # Check Internet Connection
            status = SCh.check_internet_connection()
            print(SCh.connection_message(status))
            FH.write_log(username, "Internet Check", "success" if status.ok else "warning", status.message)
        elif choice == 6:
            return Menu.MAIN
        else:
            print("Invalid choice.")
        return None
    elif current_menu == Menu.OBJECT_MANAGEMENT and role == 'admin':
        if choice == 1:
            # Create Object
            name = input("Enter object name: ")
            description = input("Enter description: ")
            ra_dec = input("Enter RA,Dec (comma separated, e.g. '12.34,56.78'): ")
            ned_code = input("Enter NED code: ")
            create_object(str(user['_id']), name, description, ra_dec, ned_code)
        elif choice == 2:
            # List Objects
            list_objects(str(user['_id']), role)
        elif choice == 3:
            # Update Object
            name = input("Enter the name of the object to update: ")
            if not name:
                print("Object name is required.")
                return None
            description = input("Enter new description (leave blank to keep current): ")
            ra_dec = input("Enter new RA,Dec (leave blank to keep current): ")
            ned_code = input("Enter new NED code (leave blank to keep current): ")
            # Only pass values if provided
            kwargs = {}
            if description: kwargs['description'] = description
            if ra_dec: kwargs['ra_dec'] = ra_dec
            if ned_code: kwargs['ned_code'] = ned_code
            update_object(name, user_id=str(user['_id']), role=role, **kwargs)
        elif choice == 4:
            # Delete Object
            name = input("Enter the name of the object to delete: ")
            if not name:
                print("Object name is required.")
                return None
            delete_object(name, user_id=str(user['_id']), role=role)
        elif choice == 5:
            return Menu.MAIN
        return None
    elif current_menu == Menu.USER_MANAGEMENT and role == 'admin':
        if choice == 1:
            # Create User
            create_user()
        elif choice == 2:
            # List Users
            list_users()
        elif choice == 3:
            # Update User
            update_user()
        elif choice == 4:
            # Delete User
            delete_user()
        elif choice == 5:
            return Menu.MAIN
        else:
            print("Invalid choice.")
        return None
    else:
        print("Access denied: Insufficient permissions.")
        FH.write_log(username, f"Access Menu {current_menu.name}", "error", "User role does not permit access")
        return None

# Get validated alt/az with input loop
def get_valid_alt_az() -> Tuple[float, float]:
    while True:
        try:
            alt = float(input("Enter Alt (Altitude) degrees (-75 to 75): "))
            az = float(input("Enter Az (Azimuth) degrees (25 to 355): "))
            alt_az_input_validation(alt, az)
            print("Valid Alt/Az input!")
            return alt, az
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

# Validate alt/az against ranges and config limits
def alt_az_input_validation(alt: float, az: float) -> bool:
    if not isinstance(alt, (float, int)) or not isinstance(az, (float, int)):
        raise ValueError("Alt and Az must be numbers")
    # Use configured limits for validation
    alt_limits = config.get('altitude_limits', [-75, 75])
    az_limits = config.get('azimuth_limits', [25, 355])
    if not (alt_limits[0] <= alt <= alt_limits[1]):
        raise ValueError(f"Alt must be between {alt_limits[0]} and {alt_limits[1]} degrees")
    if not (az_limits[0] <= az <= az_limits[1]):
        raise ValueError(f"Az must be between {az_limits[0]} and {az_limits[1]} degrees")
    if not (alt_limits[0] <= alt <= alt_limits[1]):
        raise ValueError(f"Alt out of custom limits: {alt_limits}")
    if not (az_limits[0] <= az <= az_limits[1]):
        raise ValueError(f"Az out of custom limits: {az_limits}")
    return True

# Get validated RA/Dec with input loop
def get_valid_ra_dec() -> Tuple[str, str]:
    while True:
        try:
            ra = input("Enter RA (Right Ascension) value (e.g., '00h42m30s'): ")
            dec = input("Enter Dec (Declination) value (e.g., '+41d12m00s'): ")
            ra_dec_input_validation(ra, dec)
            print("Valid RA/Dec input!")
            return ra, dec
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

# Validate RA/Dec format flexibly to match Calculations.convert_radec_to_degrees
def ra_dec_input_validation(ra: str, dec: str) -> bool:
    # Accept common string formats like '00h42m30s', '+41d12m00s', or decimal strings
    hms_regex = r"^\s*\d{1,2}h\d{1,2}m\d{1,2}(\.\d+)?s\s*$"
    dms_regex = r"^\s*[+-]?\d{1,2}d\d{1,2}m\d{1,2}(\.\d+)?s\s*$"
    decimal_regex = r"^\s*[+-]?\d+(\.\d+)?\s*$"
    ra_ok = bool(re.match(hms_regex, ra) or re.match(decimal_regex, ra))
    dec_ok = bool(re.match(dms_regex, dec) or re.match(decimal_regex, dec))
    if not ra_ok or not dec_ok:
        raise ValueError("Invalid RA/Dec. Accepts 'hhmmss'/'ddmmss' or decimal values.")
    return True

# Get validated celestial code with input loop
def get_valid_celestial_code() -> str:
    while True:
        try:
            code = input("\nEnter the code of the celestial object that you would like to track: ")
            celestial_code_input_validation(code)
            print("Valid code input!")
            return code
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

# Validate celestial code
def celestial_code_input_validation(code: str) -> bool:
    if not code.isalnum():
        raise ValueError("The code must be alphanumeric.")
    if len(code) < 3:
        raise ValueError("The code must be at least 3 characters long.")
    return True

# Main program loop
def main():
    try:
        # Initialize MongoDB logging backend
        FH.init_mongodb()
        # Ensure configuration has required defaults
        required_defaults = {
            'latitude': 0.0,
            'longitude': 0.0,
            'elevation': 0.0,
            'celestial_ping_time': 3,
            'movement_timeout': 10,
            'position_tolerance': 0.01,
            'altitude_limits': [-75, 75],
            'azimuth_limits': [25, 355],
            'clamp_to_limits': True,
            'prevent_below_horizon': True,
            'safety_alt_margin_deg': 2.0,
            'safety_az_margin_deg': 1.0,
            'invert_elevation_axis': False,
            'force_first_movement_clockwise': False,
            'tracking_in_background': False,
            'headless_tracking': False,
            'base_joint_name': 'Base_joint',
            'mount_joint_name': 'Mount_joint',
            'base_max_force': 1000.0,
            'elevation_max_force': 1500.0,
        }
        changed = False
        for k, v in required_defaults.items():
            if config.get(k) is None:
                config.update(k, v)
                changed = True
        # Optional: validate config and warn
        if not config.validate():
            logging.warning("Configuration missing keys; defaults were applied where needed.")
        # Ensure there is at least one admin user
        try:
            if users_collection is not None and not users_collection.find_one({"role": "admin"}):
                default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
                default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
                hashed_pw = generate_password_hash(default_password)
                users_collection.insert_one({
                    'username': default_username,
                    'password': hashed_pw,
                    'role': 'admin',
                    'name': 'Default',
                    'surname': 'Admin',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
                logging.warning("No admin found. Created default admin account. Change credentials immediately.")
        except Exception as e:
            logging.error(f"Failed to ensure default admin: {e}")
        user = authenticate()
        if not user:
            print("Authentication failed. Please check MongoDB connection and Users collection.")
            exit(1)
        current_menu = Menu.MAIN
        while True:
            display_menu(current_menu.value, user['role'])
            choice = get_menu_choice()
            if current_menu == Menu.MAIN and ((user['role'] == 'admin' and choice == 7) or (user['role'] == 'operator' and choice == 3)):
                FH.write_log(user['username'], "Exit", "success", "Program exited")
                TM.close()
                break
            next_menu = handle_menu_choice(current_menu, choice, user)
            current_menu = next_menu if next_menu else Menu.MAIN
    except Exception as e:
        logging.error(f"Fatal error: {e}")

if __name__ == '__main__':
    main()