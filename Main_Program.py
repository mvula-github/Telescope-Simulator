import Calculations as C, File_Handling as FH, Telescope_Movement as TM, System_Checks as SCh
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
        print("Access granted.\n")
        return True
    else:
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
    if menu_num == 0:
        display_menu(choice)
        handle_menu_choice(choice, get_menu_choice())
    elif menu_num == 1: # Telescope Control Menu
        if choice == 1: # Point To AltAz
            alt = float(input("Enter altitude degrees: "))
            az = float(input("Enter azimuth degrees: "))
            # Add functionality to move telescope here
        elif choice == 2: # Point To RaDec
            ra = input("Enter Ra value: ")
            dec = input("Enter dec value: ")
            alt, az = C.convert_radec_to_altaz(ra, dec)
            # Add functionality to move telescope here
        elif choice == 3: # Tracking
            code = input("\nEnter the code of the celestial object that you would like to track: ")
            TM.track_celestial_object(code)
        elif choice == 4: # Rest Mode
            # Add functionality to make telescope enter rest mode
            pass
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
        elif choice == 2: # Change Data Store Location
            # ADD FUNCTIONALITY TO CHANGE LOCATION WHERE DATA IS STORED
            pass
        elif choice == 3: # Change Telescope Limits
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

def main():
    while not authenticate():
        print("Incorrect credentials. Please try again.")
    
    while True:
        display_menu(0)
        choice = get_menu_choice()
        if choice == 5:  # Exit
            break
        handle_menu_choice(0, choice)

if __name__ == '__main__':
    main()