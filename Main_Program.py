import Calculations as C, File_Handling as FH, Telescope_Movement as TM, System_Checks as SCh,re
from System_Config import config
import getpass, os

# File where credentials are stored
CREDENTIALS_FILE = os.path.join("Resources", "credentials.txt")

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

def load_credentials():
    with open(CREDENTIALS_FILE, 'r') as file:
        lines = file.readlines()
        user, password = lines[0].strip(), lines[1].strip()
    return user, password

def authenticate():
    stored_user, stored_password = load_credentials()
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    if username == stored_user and password == stored_password:
        FH.write_log(username, "Login", True, "Login successful")
        print("Access granted.\n")
        return True
    else:
        FH.write_log(username, "Login", False, "Failed login attempt")
        return False

def get_menu_choice(prompt="\nEnter your choice: "):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input, please enter a number corresponding to the menu option.")

def display_menu(menu_num):
    print("\n*******************************")
    print("   Radio Telescope Control     ")
    print("*******************************\n")
    for option in MENUS.get(menu_num, []):
        print(option)

def handle_menu_choice(menu_num, choice):
    user = "admin"
    if menu_num == 0:
        display_menu(choice)
        handle_menu_choice(choice, get_menu_choice())
    elif menu_num == 1: # Telescope Control Menu
        if choice == 1: # Point To AltAz
            alt, az = get_valid_alt_az()
            
            TM.move_tel(alt, az)
            FH.write_log(user,"Telescope Movement",True, f"Moved telescope to Alt: {alt}, Az: {az}")
        elif choice == 2: # Point To RaDec
            ra = input("Enter Ra value: ")
            dec = input("Enter dec value: ")
            alt, az = C.convert_radec_to_altaz(ra, dec)
            
            TM.move_tel(alt, az)
            FH.write_log(user, "Telescope Movement",True, f"Moved telescope to RA: {ra}, Dec: {dec}")
        elif choice == 3: # Tracking
            celestial_code = get_valid_celestial_code()
            TM.track_celestial_object(celestial_code)
            FH.write_log(user,"Tracking",True, f"Started tracking celestial object: {celestial_code}")
            # End tracking
            FH.write_log(user,"Tracking",True, f"Ended tracking celestial object: {celestial_code}")
        elif choice == 4: # Rest Mode
            TM.telescope_rest()
            FH.write_log(user, "Rest Mode",True, "Rest mode entered")
    elif menu_num == 2: # Configure Settings Menu
        if choice == 1: # Change Telescope Location
            print("(Latitude, Longitude, Elevation)")
            print(f"IP: {C.get_location_and_elevation('ip')}")
            print(f"Last Saved: {C.get_location_and_elevation('stored')}")
            print("\n")

            latitude = float(input("Enter latitude: "))
            longitude = float(input("Enter longitude: "))
            elevation = float(input("Enter elevation: "))

            config.update('latitude', latitude)
            config.update('longitude', longitude)
            config.update('elevation', elevation)

            FH.write_log(user, "Change Telescope Location",True, f"Changed location to Lat: {latitude}, Long: {longitude}, Elevation: {elevation}")

        elif choice == 2: # Change Data Store Location
            # ADD FUNCTIONALITY TO CHANGE LOCATION WHERE DATA IS STORED
            pass
        elif choice == 3: # Change Telescope Limits
            print("Altitude limits:", config.get('altitude_limits'))
            print("Azimuth limits:", config.get('azimuth_limits'))
            try:
                lower_alt = float(input("Enter lower bound for altitude limits: "))
                upper_alt = float(input("Enter upper bound for altitude limits: "))
                lower_az = float(input("Enter lower bound for azimuth limits: "))
                upper_az = float(input("Enter upper bound for azimuth limits: "))
                
                # Validate input (check if the limits are valid)

                alt_limits = [lower_alt, upper_alt]
                az_limits = [lower_az, upper_az]

                config.update('altitude_limits', alt_limits)
                config.update('azimuth_limits', az_limits)

                FH.write_log(user, "Configurations changed", True, f"Telescope limits updated: Altitude {lower_alt}-{upper_alt}, Azimuth {lower_az}-{upper_az}")
            except ValueError as e:
                FH.write_log(user, "Configurations changed", False, f"Invalid input: {e}")

    elif menu_num == 3: # Coordinate System
        if choice == 1: # Convert Alt & Az to Ra & Dec
            alt = float(input("Enter altitude degrees: "))
            az = float(input("Enter azimuth degrees: "))
            ra, dec = C.convert_altaz_to_radec(alt, az)
            print(f"AltAz converted to RaDec: RA: {ra} DEC: {dec}")
        elif choice == 2: # Convert Ra & Dec to Alt & Az
            ra = input("Enter Ra value: ")
            dec = input("Enter dec value: ")
            alt, az = C.convert_radec_to_altaz(ra, dec)
            print(f"RaDec converted to AltAz: ALT: {alt} AZ: {az}")
    elif menu_num == 4: # Display Data
        if choice == 1: # Display Location
            print("(Latitude, Longitude, Elevation)")
            print(f"IP: {C.get_location_and_elevation('ip')}")
            print(f"Last Saved: {C.get_location_and_elevation('stored')}")
        elif choice == 2: # Display Telescope Logs
            FH.display_logs()
        elif choice == 3: # Display All Commands & Descriptions
            print("\nAvailable commands: \n")
            for command, description in COMMAND_DESCRIPTIONS.items():
                print(f"{command}: {description}")
        elif choice == 4: # Display Available Celestial Objects
            ra = input("Enter Ra degree: ")
            dec = input("Enter dec degree: ")
            C.list_available_celestial_objects(ra, dec, radius=0.1)
        elif choice == 5: # Check Internet Connection
            print(SCh.check_internet_connection())
 

def get_valid_alt_az():
    while True:
        try:
            alt = float(input("Enter Alt (Altitude) degrees (-90 to 90): ")) # Input alt
            az = float(input("Enter Az (Azimuth) degrees (0 to 360): ")) # Input az
            alt_az_input_validation(alt, az) # Validation for alt and az
            print("Valid Alt/Az input!") # For debuging
            return alt, az  # Return the validated values
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def alt_az_input_validation(alt, az):
    # alt validation
    if not isinstance(alt, (float, int)):
        raise ValueError("Alt (Altitude) must be a number")
    if not (-90 <= alt <= 90):
        raise ValueError("Alt (Altitude) must be between -90 and 90 degrees")
    # az validation
    if not isinstance(az, (float, int)):
        raise ValueError("Az (Azimuth) must be a number")
    if not (0 <= alt <= 360):
        raise ValueError("Az (Azimuth) must be between 0 and 360 degrees")
    return True # If user input passes validation

def get_valid_ra_dec():
    while True:
        try:
            ra = input("Enter RA (Right Ascension) value (e.g., '00h42m30s'): ") # Input ra
            dec = input("Enter Dec (Declination) value (e.g., '+41d12m00s'): ") # Input dec
            ra_dec_input_validation(ra, dec) # Validation for ra and dec
            print("Valid RA/Dec input!") # For debuging
            return ra, dec  # Return the validated values
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")

def ra_dec_input_validation(ra, dec):
    # Define regex patterns for ra and dec in the specific format
    ra_pattern = r"^\d{1,2}h\d{1,2}m\d{1,2}(\.\d+)?s$"
    dec_pattern = r"^[+-]?\d{1,2}d\d{1,2}m\d{1,2}(\.\d+)?s$"
    # ra validate
    if not re.match(ra_pattern, ra):
        raise ValueError("RA (Right Ascension) must be in the format 'hhmmss', e.g., '00h42m30s'.")
    # dec validate
    if not re.match(dec_pattern, dec):
        raise ValueError("Dec (Declination) must be in the format '+/-ddmmss', e.g., '+41d12m00s'.")
    return True  # If user input passes validation

def get_valid_celestial_code():
    while True:
        try:
            code = input("\nEnter the code of the celestial object that you would like to track: ")
            celestial_code_input_validation(code) # Validation for celestial_code
            print("Valid code input!") # For debuging
            return code  # Return the validated code
        except ValueError as e:
            print(f"Validation error: {e}. Please try again.\n")


def celestial_code_input_validation(code):
    # Check if the code is alphanumeric and not empty
    if not code.isalnum():
        raise ValueError("The code must be alphanumeric.")
    # Check the length of the code
    if len(code) < 3:
        raise ValueError("The code must be at least 3 characters long.")

    return True  # If user input passes validation

def main():
    while not authenticate():
        print("Incorrect credentials. Please try again.")
    
    while True:
        display_menu(0)
        choice = get_menu_choice()
        if choice == 5:  # Exit
            break
        handle_menu_choice( 0, choice)

if __name__ == '__main__':
    main()