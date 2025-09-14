import sys
import os
import re
import datetime
import getpass
from dotenv import load_dotenv
from pymongo import MongoClient, errors
import bcrypt
import Calculations as C
import File_Handling as FH
import Telescope_Movement as TM
import System_Checks as SCh
from System_Config import config

# Load environment variables from .env file
load_dotenv()

COMMAND_DESCRIPTIONS = {
    "Telescope Control": "Display menu responsible for telescope control functions.",
    "Configure Settings": "Display menu responsible for configuration settings.",
    "Coordinate System": "Display menu responsible for coordinate calculations and conversions.",
    "Display Data": "Display menu responsible for displaying system info.",
    "Exit": "Exit the RTOS program.",
    "Point to AltAz": "Point telescope to specific Alt (altitude) & Az (azimuth) degrees.",
    "Point To RaDec": "Point telescope to specific Ra (right ascension) & Dec (declination) values.",
    "Tracking": "Initiate tracking process to track a celestial object.",
    "Rest Mode": "Move telescope to rest mode.",
    "Change Telescope Location": "Change physical location values of telescope (Latitude, Longitude, Elevation).",
    "Change Data Store Location": "Change the location where the telescope frequency data is stored.",
    "Change Telescope Limits": "Change upper and lower altitude and azimuth degree limits of telescope limits.",
    "Convert Alt & Az to Ra & Dec": "Convert Alt (altitude) & Az (azimuth) degrees to Ra (right ascension) & Dec (declination) values.",
    "Convert Ra & Dec to Alt & Az": "Convert Ra (right ascension) & Dec (declination) values to Alt (altitude) & Az (azimuth) degrees.",
    "Display location": "Display location using IP, GPS, and the last stored location in the configuration file.",
    "Display Telescope Logs": "Display log files created by software.",
    "Display All Commands & Descriptions": "Display list of all commands in program and their descriptions.",
    "Display Available Celestial Objects": "Display list of all celestial objects that are in a certain radius from ra (right ascension) & dec (declination) values.",
    "Check Internet Connection": "Test internet connection and give feedback."
}

MENUS = {
    0: ["1. Telescope Control", "2. Configure Settings", "3. Coordinate System", "4. Display Data", "5. Exit"],
    1: ["1. Point To AltAz", "2. Point To RaDec", "3. Tracking", "4. Rest Mode"],
    2: ["1. Change Telescope Location", "2. Change Data Store Location", "3. Change Telescope Limits"],
    3: ["1. Convert Alt & Az to Ra & Dec", "2. Convert Ra & Dec to Alt & Az"],
    4: ["1. Display Location", "2. Display Telescope Logs", "3. Display All Commands & Descriptions", "4. Display Available Celestial Objects", "5. Check Internet Connection"]
}

# DATABASE CONNECTION
def connect_to_mongo():
    """Connect to MongoDB Atlas and return the client."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI not set in .env file.")

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("Connected to MongoDB Atlas.")
        return client
    except errors.ConnectionFailure:
        print("Failed to connect to MongoDB. Check MONGO_URI or network.")
        return None

# PASSWORD HANDLING
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_password(password: str, hashed) -> bool:
    # If hashed is str, convert to bytes
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), hashed)

# LOGGING USER ACTIONS 
def log_action(action_logs_collection, acting_user, action_type, target, status, details):
    """Log user actions in the action_logs collection."""
    try:
        action_logs_collection.insert_one({
            "acting_user": acting_user,
            "action_type": action_type,
            "target": target,
            "status": status,
            "details": details,
            "timestamp": datetime.datetime.now()
        })
    except errors.PyMongoError as e:
        print(f"Failed to log action: {e}")

# CRUD OPERATIONS
def create_user(users_collection, action_logs_collection, acting_user, username=None, password=None, role=None, name=None, surname=None):
    """Create a new user and log the action."""
    try:
        if not username:
            username = input("Enter new username: ").strip()
        if users_collection.find_one({"username": username}):
            print("Username already exists.")
            log_action(action_logs_collection, acting_user, "Create User", username, False, "Username already exists")
            return False

        if not password:
            password = getpass.getpass("Enter new password (min 8 chars): ").strip()
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            log_action(action_logs_collection, acting_user, "Create User", username, False, "Password too short")
            return False

        if not role:
            role_input = input("Select role (1 = Admin, 2 = Operator): ").strip()
            role = "admin" if role_input == "1" else "operator"

        if not name:
            name = input("Enter first name: ").strip()
        if not surname:
            surname = input("Enter last name: ").strip()

        username = re.sub(r"[^\w\s]", "", username)
        name = re.sub(r"[^\w\s]", "", name)
        surname = re.sub(r"[^\w\s]", "", surname)

        hashed_pw = hash_password(password)
        users_collection.insert_one({
            "username": username,
            "password": hashed_pw,
            "role": role,
            "name": name,
            "surname": surname,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
        })
        print(f"User '{username}' created as '{role}'.")
        log_action(action_logs_collection, acting_user, "Create User", username, True, f"Created user with role {role}")
        return True
    except errors.PyMongoError as e:
        print(f"Database error: {e}")
        log_action(action_logs_collection, acting_user, "Create User", username, False, f"Database error: {e}")
        return False

def read_users(users_collection, action_logs_collection, acting_user):
    """Fetch and print all users (without password) and log the action."""
    try:
        users = list(users_collection.find({}, {"password": 0}))
        if not users:
            print("No users found.")
            log_action(action_logs_collection, acting_user, "View Users", "all", True, "No users found")
            return []
        for user in users:
            print(f"{user['username']} ({user['role']}) - {user['name']} {user['surname']}")
        log_action(action_logs_collection, acting_user, "View Users", "all", True, "Viewed all users")
        return users
    except errors.PyMongoError as e:
        print(f"Database error: {e}")
        log_action(action_logs_collection, acting_user, "View Users", "all", False, f"Database error: {e}")
        return []

def update_user(users_collection, action_logs_collection, acting_user, username=None):
    """Update user details with validation and log the action."""
    try:
        if not username:
            username = input("Enter username to update: ").strip()
        user = users_collection.find_one({"username": username})
        if not user:
            print("User not found.")
            log_action(action_logs_collection, acting_user, "Update User", username, False, "User not found")
            return False

        print("Leave fields blank to keep unchanged.")
        new_username = input("New username: ").strip()
        new_password = getpass.getpass("New password (min 8 chars): ").strip()
        role_input = input("New role (1=Admin, 2=Operator, blank=skip): ").strip()
        new_role = "admin" if role_input == "1" else ("operator" if role_input == "2" else None)
        new_name = input("New first name: ").strip()
        new_surname = input("New surname: ").strip()

        update_fields = {}
        if new_username and new_username != username:
            if users_collection.find_one({"username": new_username}):
                print("New username already exists.")
                log_action(action_logs_collection, acting_user, "Update User", username, False, "New username already exists")
                return False
            update_fields["username"] = new_username
        if new_password:
            if len(new_password) < 8:
                print("Password must be at least 8 characters.")
                log_action(action_logs_collection, acting_user, "Update User", username, False, "Password too short")
                return False
            update_fields["password"] = hash_password(new_password)
        if new_role:
            update_fields["role"] = new_role
        if new_name:
            update_fields["name"] = new_name
        if new_surname:
            update_fields["surname"] = new_surname
        if update_fields:
            update_fields["updated_at"] = datetime.datetime.now()

        if update_fields:
            users_collection.update_one({"username": username}, {"$set": update_fields})
            print("User updated successfully.")
            log_action(action_logs_collection, acting_user, "Update User", username, True, f"Updated fields: {list(update_fields.keys())}")
            return True
        else:
            print("No changes made.")
            log_action(action_logs_collection, acting_user, "Update User", username, False, "No changes made")
            return False
    except errors.PyMongoError as e:
        print(f"Database error: {e}")
        log_action(action_logs_collection, acting_user, "Update User", username, False, f"Database error: {e}")
        return False

def delete_user(users_collection, action_logs_collection, acting_user, username=None):
    """Delete a user by username and log the action."""
    try:
        if not username:
            username = input("Enter username to delete: ").strip()
        result = users_collection.delete_one({"username": username})
        if result.deleted_count:
            print(f"User '{username}' deleted.")
            log_action(action_logs_collection, acting_user, "Delete User", username, True, "User deleted")
            return True
        else:
            print("User not found.")
            log_action(action_logs_collection, acting_user, "Delete User", username, False, "User not found")
            return False
    except errors.PyMongoError as e:
        print(f"Database error: {e}")
        log_action(action_logs_collection, acting_user, "Delete User", username, False, f"Database error: {e}")
        return False

# LOGIN
def login(users_collection):
    """Simple username/password login for testing."""
    attempts = 0
    while attempts < 3:
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()
        user = users_collection.find_one({"username": username})
        if user and check_password(password, user["password"]):
            print(f"Login successful. Welcome {user['name']}!")
            return user
        else:
            attempts += 1
            print(f"Invalid credentials. {3 - attempts} attempts left.")
    print("Too many failed attempts. Exiting.")
    sys.exit(1)

# TELESCOPE CONTROL FUNCTIONS 
def display_menu(menu_num, role="admin"):
    """Display menu based on menu number and user role."""
    print("\n*******************************")
    print("   Radio Telescope Control     ")
    print("*******************************\n")
    if role == "operator" and menu_num == 0:
        for option in ["1. Telescope Control", "5. Exit"]:
            print(option)
    else:
        for option in MENUS.get(menu_num, []):
            print(option)

def get_menu_choice(prompt="\nEnter your choice: "):
    """Get and validate menu choice."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input, please enter a number corresponding to the menu option.")

def handle_menu_choice(menu_num, choice, user, action_logs_collection):
    """Handle menu choices for telescope control and log actions."""
    username = user["username"]
    if menu_num == 0:
        if choice == 5:  # Exit
            print("Logging out...")
            log_action(action_logs_collection, username, "Logout", "system", True, "User logged out")
            return False
        elif choice == 1 or (user["role"] == "operator" and choice == 1):  # Telescope Control
            display_menu(1, user["role"])
            handle_menu_choice(1, get_menu_choice(), user, action_logs_collection)
        elif user["role"] == "admin" and choice in [2, 3, 4]:
            display_menu(choice, user["role"])
            handle_menu_choice(choice, get_menu_choice(), user, action_logs_collection)
        else:
            print("Invalid option or access denied.")
            log_action(action_logs_collection, username, "Invalid Menu Choice", f"menu {menu_num}", False, f"Invalid choice: {choice}")
            display_menu(0, user["role"])
            handle_menu_choice(0, get_menu_choice(), user, action_logs_collection)
    elif menu_num == 1:  # Telescope Control Menu
        if choice == 1:  # Point To AltAz
            alt, az = get_valid_alt_az()
            if TM.test_con():
                TM.move_tel(alt, az)
                FH.write_log(username, "Point To AltAz", True, f"Moved telescope to Alt: {alt}, Az: {az}")
                log_action(action_logs_collection, username, "Point To AltAz", "telescope", True, f"Moved telescope to Alt: {alt}, Az: {az}")
        elif choice == 2:  # Point To RaDec
            ra, dec = get_valid_ra_dec()
            alt, az = C.convert_radec_to_altaz(ra, dec)
            if TM.test_con():
                TM.move_tel(alt, az)
                FH.write_log(username, "Point To RaDec", True, f"Moved telescope to RA: {ra}, Dec: {dec}")
                log_action(action_logs_collection, username, "Point To RaDec", "telescope", True, f"Moved telescope to RA: {ra}, Dec: {dec}")
        elif choice == 3:  # Tracking
            celestial_code = get_valid_celestial_code()
            TM.track_celestial_object(celestial_code)
            FH.write_log(username, "Tracking", True, f"Tracking celestial object: {celestial_code}")
            log_action(action_logs_collection, username, "Tracking", "telescope", True, f"Tracking celestial object: {celestial_code}")
        elif choice == 4:  # Rest Mode
            TM.telescope_rest()
            FH.write_log(username, "Rest Mode", True, "Telescope moved to rest mode")
            log_action(action_logs_collection, username, "Rest Mode", "telescope", True, "Telescope moved to rest mode")
        display_menu(0, user["role"])
        handle_menu_choice(0, get_menu_choice(), user, action_logs_collection)
    elif menu_num == 2:  # Configure Settings Menu
        if choice == 1:  # Change Telescope Location
            print("(Latitude, Longitude, Elevation)")
            print(f"IP: {C.get_location_and_elevation('ip')}")
            print(f"Last Saved: {C.get_location_and_elevation('stored')}")
            latitude = float(input("Enter latitude: "))
            longitude = float(input("Enter longitude: "))
            elevation = float(input("Enter elevation: "))
            config.update('latitude', latitude)
            config.update('longitude', longitude)
            config.update('elevation', elevation)
            FH.write_log(username, "Change Telescope Location", True, f"Changed location to Lat: {latitude}, Long: {longitude}, Elevation: {elevation}")
            log_action(action_logs_collection, username, "Change Telescope Location", "telescope", True, f"Changed location to Lat: {latitude}, Long: {longitude}, Elevation: {elevation}")
        elif choice == 2:  # Change Data Store Location
            print("Functionality to change data store location not implemented.")
            log_action(action_logs_collection, username, "Change Data Store Location", "telescope", False, "Functionality not implemented")
        elif choice == 3:  # Change Telescope Limits
            print("Altitude limits:", config.get('altitude_limits'))
            print("Azimuth limits:", config.get('azimuth_limits'))
            lower_alt = float(input("Enter lower bound for altitude limits: "))
            upper_alt = float(input("Enter upper bound for altitude limits: "))
            lower_az = float(input("Enter lower bound for azimuth limits: "))
            upper_az = float(input("Enter upper bound for azimuth limits: "))
            alt_limits = [lower_alt, upper_alt]
            az_limits = [lower_az, upper_az]
            config.update('altitude_limits', alt_limits)
            config.update('azimuth_limits', az_limits)
            FH.write_log(username, "Change Telescope Limits", True, f"Telescope limits updated: Altitude {lower_alt}-{upper_alt}, Azimuth {lower_az}-{upper_az}")
            log_action(action_logs_collection, username, "Change Telescope Limits", "telescope", True, f"Telescope limits updated: Altitude {lower_alt}-{upper_alt}, Azimuth {lower_az}-{upper_az}")
        display_menu(0, user["role"])
        handle_menu_choice(0, get_menu_choice(), user, action_logs_collection)
    elif menu_num == 3:  # Coordinate System
        if choice == 1:  # Convert Alt & Az to Ra & Dec
            alt = float(input("Enter altitude degrees: "))
            az = float(input("Enter azimuth degrees: "))
            ra, dec = C.convert_altaz_to_radec(alt, az)
            print(f"AltAz converted to RaDec: RA: {ra} DEC: {dec}")
            FH.write_log(username, "Convert AltAz to RaDec", True, f"Converted Alt: {alt}, Az: {az} to RA: {ra}, Dec: {dec}")
            log_action(action_logs_collection, username, "Convert AltAz to RaDec", "telescope", True, f"Converted Alt: {alt}, Az: {az} to RA: {ra}, Dec: {dec}")
        elif choice == 2:  # Convert Ra & Dec to Alt & Az
            ra, dec = get_valid_ra_dec()
            alt, az = C.convert_radec_to_altaz(ra, dec)
            print(f"RaDec converted to AltAz: ALT: {alt} AZ: {az}")
            FH.write_log(username, "Convert RaDec to AltAz", True, f"Converted RA: {ra}, Dec: {dec} to Alt: {alt}, Az: {az}")
            log_action(action_logs_collection, username, "Convert RaDec to AltAz", "telescope", True, f"Converted RA: {ra}, Dec: {dec} to Alt: {alt}, Az: {az}")
        display_menu(0, user["role"])
        handle_menu_choice(0, get_menu_choice(), user, action_logs_collection)
    elif menu_num == 4:  # Display Data
        if choice == 1:  # Display Location
            print("(Latitude, Longitude, Elevation)")
            print(f"IP: {C.get_location_and_elevation('ip')}")
            print(f"Last Saved: {C.get_location_and_elevation('stored')}")
            FH.write_log(username, "Display Location", True, "Displayed telescope location")
            log_action(action_logs_collection, username, "Display Location", "telescope", True, "Displayed telescope location")
        elif choice == 2:  # Display Telescope Logs
            FH.display_logs()
            FH.write_log(username, "Display Telescope Logs", True, "Displayed telescope logs")
            log_action(action_logs_collection, username, "Display Telescope Logs", "telescope", True, "Displayed telescope logs")
        elif choice == 3:  # Display All Commands & Descriptions
            print("\nAvailable commands: \n")
            for command, description in COMMAND_DESCRIPTIONS.items():
                print(f"{command}: {description}")
            FH.write_log(username, "Display Commands", True, "Displayed all commands and descriptions")
            log_action(action_logs_collection, username, "Display Commands", "telescope", True, "Displayed all commands and descriptions")
        elif choice == 4:  # Display Available Celestial Objects
            ra = input("Enter Ra degree: ")
            dec = input("Enter dec degree: ")
            C.list_available_celestial_objects(ra, dec, radius=0.1)
            FH.write_log(username, "Display Celestial Objects", True, f"Displayed celestial objects near RA: {ra}, Dec: {dec}")
            log_action(action_logs_collection, username, "Display Celestial Objects", "telescope", True, f"Displayed celestial objects near RA: {ra}, Dec: {dec}")
        elif choice == 5:  # Check Internet Connection
            result = SCh.check_internet_connection()
            print(result)
            FH.write_log(username, "Check Internet Connection", True, f"Internet connection check: {result}")
            log_action(action_logs_collection, username, "Check Internet Connection", "telescope", True, f"Internet connection check: {result}")
        display_menu(0, user["role"])
        handle_menu_choice(0, get_menu_choice(), user, action_logs_collection)
    return True

def get_valid_alt_az():
    while True:
        try:
            alt = float(input("Enter Alt (Altitude) degrees (-90 to 90): "))
            az = float(input("Enter Az (Azimuth) degrees (0 to 360): "))
            alt_az_input_validation(alt, az)
            print("Valid Alt/Az input!")
            return alt, az
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def alt_az_input_validation(alt, az):
    if not isinstance(alt, (float, int)):
        raise ValueError("Alt (Altitude) must be a number")
    if not (-90 <= alt <= 90):
        raise ValueError("Alt (Altitude) must be between -90 and 90 degrees")
    if not isinstance(az, (float, int)):
        raise ValueError("Az (Azimuth) must be a number")
    if not (0 <= az <= 360):
        raise ValueError("Az (Azimuth) must be between 0 and 360 degrees")
    return True

def get_valid_ra_dec():
    while True:
        try:
            ra = input("Enter RA (Right Ascension) value (e.g., '00h42m30s'): ")
            dec = input("Enter Dec (Declination) value (e.g., '+41d12m00s'): ")
            ra_dec_input_validation(ra, dec)
            print("Valid RA/Dec input!")
            return ra, dec
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def ra_dec_input_validation(ra, dec):
    ra_pattern = r"^\d{1,2}h\d{1,2}m\d{1,2}(\.\d+)?s$"
    dec_pattern = r"^[+-]?\d{1,2}d\d{1,2}m\d{1,2}(\.\d+)?s$"
    if not re.match(ra_pattern, ra):
        raise ValueError("RA (Right Ascension) must be in the format 'hhmmss', e.g., '00h42m30s'.")
    if not re.match(dec_pattern, dec):
        raise ValueError("Dec (Declination) must be in the format '+/-ddmmss', e.g., '+41d12m00s'.")
    return True

def get_valid_celestial_code():
    while True:
        try:
            code = input("\nEnter the code of the celestial object that you would like to track: ")
            celestial_code_input_validation(code)
            print("Valid code input!")
            return code
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def celestial_code_input_validation(code):
    if not code.isalnum():
        raise ValueError("The code must be alphanumeric.")
    if len(code) < 3:
        raise ValueError("The code must be at least 3 characters long.")
    return True

# MENUS 
def admin_menu(user, users_collection, action_logs_collection):
    while True:
        print(f"\n=== Admin Portal: {user['name']} ===")
        print("1. Create User")
        print("2. View All Users")
        print("3. Update User")
        print("4. Delete User")
        print("5. Radio Telescope Control")
        print("6. Logout")
        choice = input("Select option: ").strip()
        if choice == "1":
            create_user(users_collection, action_logs_collection, user["username"])
        elif choice == "2":
            read_users(users_collection, action_logs_collection, user["username"])
        elif choice == "3":
            update_user(users_collection, action_logs_collection, user["username"])
        elif choice == "4":
            delete_user(users_collection, action_logs_collection, user["username"])
        elif choice == "5":
            display_menu(0, user["role"])
            if not handle_menu_choice(0, get_menu_choice(), user, action_logs_collection):
                break
        elif choice == "6":
            print("Logging out...")
            log_action(action_logs_collection, user["username"], "Logout", "system", True, "User logged out")
            break
        else:
            print("Invalid option.")
            log_action(action_logs_collection, user["username"], "Invalid Menu Choice", "admin_menu", False, f"Invalid choice: {choice}")

def operator_menu(user, action_logs_collection):
    while True:
        display_menu(0, user["role"])
        choice = get_menu_choice()
        if not handle_menu_choice(0, choice, user, action_logs_collection):
            break

# DEFAULT ADMIN BOOTSTRAP 
def ensure_admin(users_collection, action_logs_collection):
    if not users_collection.find_one({"role": "admin"}):
        print("No admin found. Creating default admin (username=admin, password=admin123)")
        create_user(users_collection, action_logs_collection, "system", username="admin", password="admin123", role="admin", name="Default", surname="Admin")

# MAIN 
def main():
    client = connect_to_mongo()
    if not client:
        sys.exit(1)

    try:
        db = client["celestiCodeServerDB"]
        users_collection = db["users"]
        action_logs_collection = db["action_logs"]

        ensure_admin(users_collection, action_logs_collection)

        print("=== CelestiCode User Management System ===")
        user = login(users_collection)

        if user["role"] == "admin":
            admin_menu(user, users_collection, action_logs_collection)
        else:
            operator_menu(user, action_logs_collection)
    finally:
        client.close()

if __name__ == "__main__":
    main()