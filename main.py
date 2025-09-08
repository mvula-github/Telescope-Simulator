import File_Handling as FH
import Telescope_Movement as TM
import Calculations as C
import System_Checks as SCh
from System_Config import config

import getpass
from enum import Enum
from typing import Optional, Tuple
import re
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import os
import bcrypt
from datetime import datetime
# Load .env
load_dotenv()

# MongoDB setup for Users collection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'celestiCodeServerDB')
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db['users']
except PyMongoError as e:
    print(f"Error: Failed to connect to MongoDB for Users collection: {e}")
    exit(1)

# Initialize MongoDB and SimConnection
try:
    FH.init_mongodb()
except RuntimeError as e:
    print(f"Error: {e}")
    exit(1)
conn = TM.SimConnection()

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

MENUS = {
    0: {
        'admin': ["1. Telescope Control", "2. Configure Settings", "3. Coordinate System", "4. User Management", "5. Display Data", "6. Exit"],
        'operator': ["1. Telescope Control", "2. Display Data", "3. Exit"]
    },
    1: ["1. Point To AltAz", "2. Point To RaDec", "3. Tracking", "4. Rest Mode"],
    2: ["1. Change Telescope Location", "2. Change Data Store Location", "3. Change Telescope Limits"],
    3: ["1. Convert Alt & Az to Ra & Dec", "2. Convert Ra & Dec to Alt & Az"],
    4: ["1. Create User", "2. List Users", "3. Update User", "4. Delete User"],
    5: ["1. Display Location", "2. Display Telescope Logs", "3. Display All Commands & Descriptions", 
        "4. Display Available Celestial Objects", "5. Check Internet Connection"]
}

class Menu(Enum):
    MAIN = 0
    TELESCOPE = 1
    CONFIG = 2
    COORDS = 3
    USER_MANAGEMENT = 4
    DISPLAY = 5

def authenticate() -> Optional[dict]:
    """Authenticate user against Users collection with retry limit."""
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            username = input("Enter username: ")
            password = getpass.getpass("Enter password: ")
            print(f"DEBUG: Querying for username: {username}")
            user = users_collection.find_one({"username": username})
            print(f"DEBUG: Found user: {user}")
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                FH.write_log(username, "Login", "success", f"Login successful as {user['role']}")
                print(f"Access granted as {user['role']}.\n")
                return user
            else:
                attempts += 1
                remaining = max_attempts - attempts
                FH.write_log(username, "Login", "error", f"Failed login attempt. {remaining} attempts remaining.")
                print(f"Incorrect credentials. {remaining} attempts remaining.")
        except PyMongoError as e:
            print(f"Error: Failed to authenticate due to MongoDB error: {e}")
            return None
    print("Maximum login attempts reached. Exiting.")
    exit(1)

def create_user():
    """Create a new user."""
    try:
        name = input("Enter name: ")
        surname = input("Enter surname: ")
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        role = input("Enter role (admin/operator): ").lower()
        if role not in ['admin', 'operator']:
            print("Invalid role. Must be 'admin' or 'operator'.")
            return
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data = {
            'userId': str(len(list(users_collection.find())) + 1),
            'name': name,
            'surname': surname,
            'username': username,
            'password': hashed_password,
            'role': role,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        users_collection.insert_one(user_data)
        print(f"User '{username}' created successfully.")
        FH.write_log("admin", "Create User", "success", f"Created user '{username}' with role '{role}'")
    except PyMongoError as e:
        print(f"Error creating user: {e}")
        FH.write_log("admin", "Create User", "error", str(e))
    except Exception as e:
        print(f"Unexpected error: {e}")

def list_users():
    """List all users."""
    try:
        users = list(users_collection.find().sort('created_at', 1))
        if not users:
            print("No users found.")
            return
        print("\nUser List:")
        print("-" * 80)
        print(f"{'ID':<5} {'Name':<15} {'Username':<15} {'Role':<10} {'Created At':<20}")
        print("-" * 80)
        for user in users:
            print(f"{user['userId']:<5} {user['name']:<15} {user['username']:<15} {user['role']:<10} {user['created_at'].strftime('%Y-%m-%d %H:%M:%S'):<20}")
        print("-" * 80)
        FH.write_log("admin", "List Users", "success", "Listed all users")
    except PyMongoError as e:
        print(f"Error listing users: {e}")
        FH.write_log("admin", "List Users", "error", str(e))

def update_user():
    """Update an existing user."""
    try:
        username = input("Enter username to update: ")
        user = users_collection.find_one({"username": username})
        if not user:
            print("User not found.")
            return
        print(f"Current user: Name: {user['name']}, Surname: {user['surname']}, Role: {user['role']}")
        name = input(f"Enter new name (current: {user['name']}): ") or user['name']
        surname = input(f"Enter new surname (current: {user['surname']}): ") or user['surname']
        new_password = getpass.getpass("Enter new password (leave blank to keep current): ")
        role = input(f"Enter new role (current: {user['role']}): ").lower() or user['role']
        if role not in ['admin', 'operator']:
            print("Invalid role. Must be 'admin' or 'operator'.")
            return
        update_data = {
            'name': name,
            'surname': surname,
            'role': role,
            'updated_at': datetime.now()
        }
        if new_password:
            update_data['password'] = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        users_collection.update_one({"username": username}, {"$set": update_data})
        print(f"User '{username}' updated successfully.")
        FH.write_log("admin", "Update User", "success", f"Updated user '{username}'")
    except PyMongoError as e:
        print(f"Error updating user: {e}")
        FH.write_log("admin", "Update User", "error", str(e))
    except Exception as e:
        print(f"Unexpected error: {e}")

def delete_user():
    """Delete an existing user."""
    try:
        username = input("Enter username to delete: ")
        user = users_collection.find_one({"username": username})
        if not user:
            print("User not found.")
            return
        if user['role'] == 'admin' and input("This is an admin user. Are you sure? (y/n): ").lower() != 'y':
            print("Deletion cancelled.")
            return
        users_collection.delete_one({"username": username})
        print(f"User '{username}' deleted successfully.")
        FH.write_log("admin", "Delete User", "success", f"Deleted user '{username}'")
    except PyMongoError as e:
        print(f"Error deleting user: {e}")
        FH.write_log("admin", "Delete User", "error", str(e))
    except Exception as e:
        print(f"Unexpected error: {e}")

def get_menu_choice(prompt: str = "\nEnter your choice: ") -> int:
    """Get validated integer choice."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input, please enter a number corresponding to the menu option.")

def display_menu(menu_num: int, role: str):
    """Display menu options based on user role."""
    print("\n*******************************")
    print("   Radio Telescope Control     ")
    print("*******************************\n")
    if menu_num == 0:
        for option in MENUS[menu_num][role]:
            print(option)
    else:
        for option in MENUS.get(menu_num, []):
            print(option)

def handle_menu_choice(current_menu: Menu, choice: int, user: dict) -> Optional[Menu]:
    """Handle menu choice and return next menu if sub-menu."""
    username = user['username']
    role = user['role']
    
    if current_menu == Menu.MAIN:
        if role == 'operator':
            if choice == 1:
                return Menu.TELESCOPE
            elif choice == 2:
                return Menu.DISPLAY
            elif choice == 3:
                return None  # Exit
            else:
                print("Invalid choice.")
                return Menu.MAIN
        # Admin choices
        if choice == 1:
            return Menu.TELESCOPE
        elif choice == 2:
            return Menu.CONFIG
        elif choice == 3:
            return Menu.COORDS
        elif choice == 4:
            return Menu.USER_MANAGEMENT
        elif choice == 5:
            return Menu.DISPLAY
        elif choice == 6:
            return None  # Exit
        else:
            print("Invalid choice.")
            return Menu.MAIN
    elif current_menu == Menu.TELESCOPE:
        if choice == 1:  # Point To AltAz
            alt, az = get_valid_alt_az()
            try:
                if TM.test_con():
                    TM.move_tel(alt, az)
                    FH.write_log(username, "Point To AltAz", "success", f"Pointed to Alt: {alt}, Az: {az}")
                else:
                    FH.write_log(username, "Point To AltAz", "error", "Connection failed")
            except Exception as e:
                FH.write_log(username, "Point To AltAz", "error", str(e))
        elif choice == 2:  # Point To RaDec
            ra, dec = get_valid_ra_dec()
            try:
                alt, az = C.convert_radec_to_altaz(ra, dec)
                if TM.test_con():
                    TM.move_tel(alt, az)
                    FH.write_log(username, "Point To RaDec", "success", f"Pointed to RA: {ra}, Dec: {dec} (Alt: {alt}, Az: {az})")
                else:
                    FH.write_log(username, "Point To RaDec", "error", "Connection failed")
            except Exception as e:
                FH.write_log(username, "Point To RaDec", "error", str(e))
        elif choice == 3:  # Tracking
            code = get_valid_celestial_code()
            try:
                TM.track_celestial_object(code)
                FH.write_log(username, "Tracking", "success", f"Started tracking {code}")
            except Exception as e:
                FH.write_log(username, "Tracking", "error", str(e))
        elif choice == 4:  # Rest Mode
            try:
                TM.telescope_rest()
                FH.write_log(username, "Rest Mode", "success", "Entered rest mode (facing straight up)")
            except Exception as e:
                FH.write_log(username, "Rest Mode", "error", str(e))
        return None
    elif current_menu == Menu.CONFIG and role == 'admin':
        if choice == 1:  # Change Telescope Location
            print("(Latitude, Longitude, Elevation)")
            print(f"IP: {C.get_location_and_elevation('ip')}")
            print(f"Last Saved: {C.get_location_and_elevation('stored')}")
            print("\n")
            try:
                latitude = float(input("Enter latitude: "))
                longitude = float(input("Enter longitude: "))
                elevation = float(input("Enter elevation: "))
                config.update('latitude', latitude)
                config.update('longitude', longitude)
                config.update('elevation', elevation)
                FH.write_log(username, "Change Telescope Location", "success", f"Changed to Lat: {latitude}, Long: {longitude}, Elevation: {elevation}")
            except ValueError as e:
                FH.write_log(username, "Change Telescope Location", "error", str(e))
        elif choice == 2:  # Change Data Store Location
            new_path = input("Enter new data store path: ").strip()
            valid, msg = FH.is_valid_directory(new_path)
            if valid:
                config.update('data_store_path', new_path)
                FH.write_log(username, "Change Data Store Location", "success", f"Updated to {new_path}")
                print("Path updated.")
            else:
                FH.write_log(username, "Change Data Store Location", "warning", f"Invalid path: {msg}")
                print(f"Invalid path: {msg}")
        elif choice == 3:  # Change Telescope Limits
            print("Altitude limits:", config.get('altitude_limits'))
            print("Azimuth limits:", config.get('azimuth_limits'))
            try:
                lower_alt = float(input("Enter lower bound for altitude limits: "))
                upper_alt = float(input("Enter upper bound for altitude limits: "))
                lower_az = float(input("Enter lower bound for azimuth limits: "))
                upper_az = float(input("Enter upper bound for azimuth limits: "))
                if lower_alt >= upper_alt or lower_az >= upper_az:
                    raise ValueError("Lower bound must be less than upper bound")
                alt_limits = [lower_alt, upper_alt]
                az_limits = [lower_az, upper_az]
                config.update('altitude_limits', alt_limits)
                config.update('azimuth_limits', az_limits)
                FH.write_log(username, "Change Telescope Limits", "success", f"Updated Altitude {lower_alt}-{upper_alt}, Azimuth {lower_az}-{upper_az}")
            except ValueError as e:
                FH.write_log(username, "Change Telescope Limits", "error", str(e))
        return None
    elif current_menu == Menu.COORDS and role == 'admin':
        if choice == 1:  # Convert Alt & Az to Ra & Dec
            try:
                alt = float(input("Enter altitude degrees: "))
                az = float(input("Enter azimuth degrees: "))
                ra, dec = C.convert_altaz_to_radec(alt, az)
                print(f"AltAz converted to RaDec: RA: {ra} DEC: {dec}")
                FH.write_log(username, "Convert AltAz to RaDec", "success", f"Converted Alt: {alt}, Az: {az} to RA: {ra}, Dec: {dec}")
            except ValueError as e:
                FH.write_log(username, "Convert AltAz to RaDec", "error", str(e))
        elif choice == 2:  # Convert Ra & Dec to Alt & Az
            ra = input("Enter Ra value: ")
            dec = input("Enter dec value: ")
            try:
                alt, az = C.convert_radec_to_altaz(ra, dec)
                print(f"RaDec converted to AltAz: ALT: {alt} AZ: {az}")
                FH.write_log(username, "Convert RaDec to AltAz", "success", f"Converted RA: {ra}, Dec: {dec} to Alt: {alt}, Az: {az}")
            except ValueError as e:
                FH.write_log(username, "Convert RaDec to AltAz", "error", str(e))
        return None
    elif current_menu == Menu.USER_MANAGEMENT and role == 'admin':
        if choice == 1:
            create_user()
        elif choice == 2:
            list_users()
        elif choice == 3:
            update_user()
        elif choice == 4:
            delete_user()
        return None
    elif current_menu == Menu.DISPLAY:
        if choice == 1:  # Display Location
            print("(Latitude, Longitude, Elevation)")
            print(f"IP: {C.get_location_and_elevation('ip')}")
            print(f"Last Saved: {C.get_location_and_elevation('stored')}")
            FH.write_log(username, "Display Location", "success", "Displayed location info")
        elif choice == 2:  # Display Telescope Logs
            FH.display_logs()
        elif choice == 3:  # Display All Commands & Descriptions
            print("\nAvailable commands: \n")
            for command, description in COMMAND_DESCRIPTIONS.items():
                print(f"{command}: {description}")
        elif choice == 4:  # Display Available Celestial Objects
            ra = input("Enter Ra degree: ")
            dec = input("Enter dec degree: ")
            try:
                C.list_available_celestial_objects(ra, dec, radius=0.1)
                FH.write_log(username, "Display Available Celestial Objects", "success", f"Listed objects near RA: {ra}, Dec: {dec}")
            except Exception as e:
                FH.write_log(username, "Display Available Celestial Objects", "error", str(e))
        elif choice == 5:  # Check Internet Connection
            success, msg = SCh.check_internet_connection()
            level = "success" if success else "warning"
            print(msg)
            FH.write_log(username, "Check Internet Connection", level, msg)
        return None
    else:
        print("Access denied: Insufficient permissions.")
        FH.write_log(username, f"Access Menu {current_menu.name}", "error", "User role does not permit access")
        return None

def get_valid_alt_az() -> Tuple[float, float]:
    """Get validated alt/az with input loop."""
    while True:
        try:
            alt = float(input("Enter Alt (Altitude) degrees (-90 to 90): "))
            az = float(input("Enter Az (Azimuth) degrees (0 to 360): "))
            alt_az_input_validation(alt, az)
            print("Valid Alt/Az input!")
            return alt, az
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def alt_az_input_validation(alt: float, az: float) -> bool:
    """Validate alt/az against ranges and config limits."""
    if not isinstance(alt, (float, int)) or not isinstance(az, (float, int)):
        raise ValueError("Alt and Az must be numbers")
    if not (-90 <= alt <= 90):
        raise ValueError("Alt must be between -90 and 90 degrees")
    if not (0 <= az <= 360):
        raise ValueError("Az must be between 0 and 360 degrees")
    alt_limits = config.get('altitude_limits', [-90, 90])
    az_limits = config.get('azimuth_limits', [0, 360])
    if not (alt_limits[0] <= alt <= alt_limits[1]):
        raise ValueError(f"Alt out of custom limits: {alt_limits}")
    if not (az_limits[0] <= az <= az_limits[1]):
        raise ValueError(f"Az out of custom limits: {az_limits}")
    return True

def get_valid_ra_dec() -> Tuple[str, str]:
    """Get validated RA/Dec with input loop."""
    while True:
        try:
            ra = input("Enter RA (Right Ascension) value (e.g., '00h42m30s'): ")
            dec = input("Enter Dec (Declination) value (e.g., '+41d12m00s'): ")
            ra_dec_input_validation(ra, dec)
            print("Valid RA/Dec input!")
            return ra, dec
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def ra_dec_input_validation(ra: str, dec: str) -> bool:
    """Validate RA/Dec format with regex."""
    ra_pattern = r"^\d{1,2}h\d{1,2}m\d{1,2}(\.\d+)?s$"
    dec_pattern = r"^[+-]?\d{1,2}d\d{1,2}m\d{1,2}(\.\d+)?s$"
    if not re.match(ra_pattern, ra):
        raise ValueError("RA must be in the format 'hhmmss', e.g., '00h42m30s'.")
    if not re.match(dec_pattern, dec):
        raise ValueError("Dec must be in the format '+/-ddmmss', e.g., '+41d12m00s'.")
    return True

def get_valid_celestial_code() -> str:
    """Get validated celestial code with input loop."""
    while True:
        try:
            code = input("\nEnter the code of the celestial object that you would like to track: ")
            celestial_code_input_validation(code)
            print("Valid code input!")
            return code
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def celestial_code_input_validation(code: str) -> bool:
    """Validate celestial code."""
    if not code.isalnum():
        raise ValueError("The code must be alphanumeric.")
    if len(code) < 3:
        raise ValueError("The code must be at least 3 characters long.")
    return True

def main():
    """Main program loop."""
    user = None
    user = authenticate()
    if not user:
        print("Authentication failed. Please check MongoDB connection and Users collection.")
        exit(1)
    
    current_menu = Menu.MAIN
    while True:
        display_menu(current_menu.value, user['role'])
        choice = get_menu_choice()
        if current_menu == Menu.MAIN and ((user['role'] == 'admin' and choice == 6) or (user['role'] == 'operator' and choice == 3)):
            FH.write_log(user['username'], "Exit", "success", "Program exited")
            conn.close()
            break
        next_menu = handle_menu_choice(current_menu, choice, user)
        current_menu = next_menu if next_menu else Menu.MAIN

if __name__ == '__main__':
    main()