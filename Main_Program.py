import os, string

# Custom libraries
import Calculations as C, File_Handling as FH, Telescope_Movement as TM

USER, PASSWORD = '', ''

COMMAND_DESCRIPTIONS = {
        "telescope_control": "Control telescope movement and position.",
        "data_file_management": "Manage data and files related to observations and telescope operations.",
        "coordinate_systems": "Work with different coordinate systems for astronomical objects.",
        "change_directory": "Change the current working directory.",
        "display_logs": "Display system logs and records.",
        "exit": "Terminate the program.",
        "altaz_control": "Point the telescope at a specific point by using AltAz degrees.",
        "radec_control": "Point the telescope at a specific point by using Ra and Dec values.",
        "tracking": "Continuously adjust the telescope's position to follow a celestial object.",
        "rest_mode": "Park the telescope in a safe position.",
        "reporting": "Generate reports based on collected data.",
        "file_path": "Specify the location for saving data files.",
        "set_location": "Define the telescope's geographic location.",
        "celestial_to_altaz_conversion": "Convert from celestial coordinates (ra and dec) to altaz degrees.",
        "altaz_to_celestial_conversion": "Convert from alt az degrees to celestial coordinates (ra and dec)."
    }

COMMAND_DESCRIPTIONS = {
    "": "",
    "": ""
}

MAIN_MENU = ["1. Telescope Control", 
            "2. Configure Settings",
            "3. Coordinate Systems",
            "4. Display Data",
            "5. Exit"]

TELESCOPE_CONTROL_MENU = ["1. Point To AltAz",
                        "2. Point To RaDec",
                        "3. Tracking",
                        "4. Rest Mode"]

CONFIG_SETTINGS_MENU = ["1. Change Location",
                        "2. Change Location where Data is Stored"]

COORDINATE_MENU =["1. Convert Alt & Az to Ra & Dec",
                "2. Convert Ra & Dec to Alt & Az"]

DISPLAY_SYS_DATA_MENU = ["1. Display Location",
                        "2. Display Telescope Logs",
                        "3. Display All Commands & Descriptions"]

# def display_menu():
#     print("\n")

#     print("*******************************")
#     print("   Radio Telescope Control     ")
#     print("*******************************")
#     print("1. Telescope Control")
#     print("2. Data Management")
#     print("3. Coordinate Systems")
#     print("4. cd")
#     print("5. Display Logs")
#     print("6. Exit")

#     print("\n")

def display_menu(menu_num):
    if menu_num == 0: # Main Menu
        print("*******************************")
        print("   Radio Telescope Control     ")
        print("*******************************")

        for i in MAIN_MENU:
            print(i)
    elif menu_num == 1: # Telescope Control Menu
        for i in TELESCOPE_CONTROL_MENU:
            print(i)
    elif menu_num == 2: # Configure Settings Menu
        for i in CONFIG_SETTINGS_MENU:
            print(i)
    elif menu_num == 3: # Coordinate Menu
        for i in COORDINATE_MENU:
            print(i)
    elif menu_num == 4: # Display System Data Menu
        for i in DISPLAY_SYS_DATA_MENU:
            print(i)

def display_COMMAND_DESCRIPTIONS(COMMAND_DESCRIPTIONS):
    for key, value in COMMAND_DESCRIPTIONS.items():
        print(f"{key}: {value}")

def __main__():
    USER = input("Enter your username: ")
    PASSWORD = input("Enter your password: ")
    print("\n")

    while True:
        display_menu(0) # Display main menu
        choice = int(input("\nEnter your choice: ")) # Input to select menu

        print("\n")
        display_menu(choice)

        if choice == 1: # Telescope control
            pass
        elif choice == 2: # Configure settings
            pass
        elif choice == 3: # Coordinate system
            pass
        elif choice == 4: # Display system data
            pass
        elif choice == 5: # Exit
            exit()
        else:
            print("Invalid option, please enter the number next to the menu item.")
        
        print("\n")

def __test__():
    user = input("Enter your username: ") # Get username for logging

    while True:
        display_menu() # Display the main menu
        # Get user input for main menu choice
        choice = input("Enter your choice: ")
        print("\n")
        if choice == '1':
            print("Telescope Control Menu:")
            print("1. Insert AltAz degrees")
            print("2. Insert Ra and Dec values")
            print("3. Tracking")
            print("4. Rest Mode")
            print("\n")
            tc_choice = input("Enter your choice: ")
            if tc_choice == "1":
                print(COMMAND_DESCRIPTIONS["altaz_control"])

                alt = int(input("Alt degrees (vertical control): "))
                az = int(input("Az degrees (horisontal control): "))

                # ADD CODE TO MOVE TELESCOPE

                FH.write_log(user,"AltAz Control","AltAz control initiated")
            elif tc_choice == "2":
                print(COMMAND_DESCRIPTIONS["radec_control"])
                
                ra = int(input("Ra value (Right Ascension): "))
                dec = int(input("Dec value (Declination): "))
                
                alt, az = C.convert_radec_to_altaz(ra, dec)

                # ADD CODE TO MOVE TELESCOPE

                FH.write_log(user, "Ra Dec Control", "Ra Dec Control initiated")
            elif tc_choice == "3":
                print(COMMAND_DESCRIPTIONS["tracking"])
                
                code = input("Insert the code of the object you would like to track: ")
                TM.track_celestial_object(code)

                FH.write_log(user, "Tracking", "Tracking initiated")
            elif tc_choice == "4":
                print(COMMAND_DESCRIPTIONS["rest_mode"])
                
                TM.telescope_rest()

                FH.write_log(user, "Rest Mode", "Rest Mode initiated")
            else:
                print("Invalid choice")

        elif choice == '2':
            print("Data Management Menu:")
            print("1. Reporting")
            print("2. File Path")
            print("\n")
            dm_choice = input("Enter your choice: ")
            if dm_choice == "1":
                print(COMMAND_DESCRIPTIONS["reporting"])
                # Replace with actual reporting logic
                FH.write_log(user, "Reporting", "Report Generation initiated")
            elif dm_choice == "2":
                print(COMMAND_DESCRIPTIONS["file_path"])
                FH.write_log(user, "File Path", "Changed the File Path ")
                # Replace with actual file path setting logic
            else:
                print("Invalid choice")

        elif choice == '3':
            print("Coordinate Systems Menu:")
            print("1. Set Location")
            print("2. Convert Celestial Frame to AltAz Degrees")
            print("3. Convert AltAz Degrees to Celestial Frame")
            print("\n")
            cs_choice = input("Enter your choice: ")
            if cs_choice == "1":
                print(COMMAND_DESCRIPTIONS["set_location"])
                FH.write_log(user, "Set Location", "Defined the Geographic Location of the Telescope ")
                # add set locations functionality
            elif cs_choice == "2":
                print(COMMAND_DESCRIPTIONS["celestial_to_altaz_conversion"], '\n')
                ra = float(input("Enter the right ascesion (ra) value: "))
                dec = float(input("Enter the declination (dec) value: "))

                alt_deg, az_deg = C.celestial_to_altaz(ra, dec)

                print(f"Current Location: {C.get_location_and_elevation()}")
                print(f"Altitude: {alt_deg:.2f} degrees, Azimuth: {az_deg:.2f} degrees")
                FH.write_log(user, "Convert Celestial Frame to AltAz Degrees", f"Celestial to Altaz Conversion: {ra}, {dec} -> {alt_deg:.2f}, {az_deg:.2f}")
            elif cs_choice == "3":
                print(COMMAND_DESCRIPTIONS["altaz_to_celestial_conversion"])
                alt = float(input("Enter the altitude (alt) value: "))
                az = float(input("Enter the azimuth (az) value: "))

                ra, dec = C.altaz_to_celestial(alt, az)

                print(f"Current Location: {C.get_location_and_elevation()}")
                print(f"Celestial Coordinates (ra, dec): ({ra}, {dec})")
                FH.write_log(user, "Convert AltAz Degrees to Celestial Frame", f"Altaz to Celestial Conversion: {alt}, {az} -> {ra:.2f}, {dec:.2f}")
            else:
                print("Invalid choice")

        elif choice == '4':
            print(COMMAND_DESCRIPTIONS["change_directory"])
            directory = input("Enter new directory: ")
            try:
                os.chdir(directory)
                FH.write_log(user, "Change Directory", f"Changed directory to: {os.getcwd()}")
                print(f"Changed directory to: {os.getcwd()}")
            except OSError:
                print("Directory change failed.")
                FH.write_log(user, "Change Directory", f"Directory change failed: {directory}")

        elif choice == "5":
            print(COMMAND_DESCRIPTIONS["display_logs"], '\n')
            FH.display_logs()
        elif choice == "6":
            print(COMMAND_DESCRIPTIONS["exit"])
            FH.write_log(user,"Exit","Terminated the program")
            exit()
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    __main__()