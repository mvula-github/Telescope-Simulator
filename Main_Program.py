import Calculations as C, File_Handling as FH, Telescope_Movement as TM

USER, PASSWORD = 'f', 'f'

COMMAND_DESCRIPTIONS = {
    "Telescope Control": "Display menu responsible for telescope control functions. ",
    "Configure Settings": "Display menu responsible for configuration settings. ",
    "Coordinate System": "Display menu responsible for coordinate calculations and conversions. ",
    "Display Data": "Display menu responsible for displaying system info. ",
    "Exit": "Exit the RTOS program. ",
    "Point to AltAz": "Point telescope to specific Alt (altitude) & Az (azimuth) degrees. ",
    "Point To RaDec": "Point telescope to specific Ra (right ascension) & Dec (declination) values. ",
    "Tracking": "Initiate tracking process to track a celestial object. ",
    "Rest Mode": "Move telescope to rest mode. ",
    "Back": "Go back to the previous menu. ",
    "Change Telescope Location": "Change physical location values of telescope (Latitude, Longitude, Elevation). ",
    "Change Data Location": "Change the location where the telescope frequency data is stored. ",
    "Convert Alt & Az to Ra & Dec": "Convert Alt (altitude) & Az (azimuth) degrees to Ra (right ascension) & Dec (declination) values.",
    "Convert Ra & Dec to Alt & Az": "Convert Ra (right ascension) & Dec (declination) values to Alt (altitude) & Az (azimuth) degrees.",
    "Display location": "Display location using IP, GPS, and the last stored location in the configuration file. ",
    "Display Telescope Logs": "Display log files created by software. ",
    "Display All Commands & Descriptions": "Display list of all commands in program and their descriptions. "
}

MAIN_MENU = ["1. Telescope Control",
            "2. Configure Settings",
            "3. Coordinate System",
            "4. Display Data",
            "5. Exit"]

TELESCOPE_CONTROL_MENU = ["1. Point To AltAz",
                        "2. Point To RaDec",
                        "3. Tracking",
                        "4. Rest Mode",
                        "5. back"]

CONFIG_SETTINGS_MENU = ["1. Change Telescope Location",
                        "2. Change Data Location",
                        "3. back"]

COORDINATE_MENU = ["1. Convert Alt & Az to Ra & Dec",
                "2. Convert Ra & Dec to Alt & Az",
                "3. back"]

DISPLAY_SYS_DATA_MENU = ["1. Display Location",
                        "2. Display Telescope Logs",
                        "3. Display All Commands & Descriptions",
                        "4. back"]

def display_menu(menu_num):
    print("\n")

    if menu_num == 0: # Main Menu
        print("\n")
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

def telescope_control_functions(choice):
    if choice == 1: # Point to altaz 
        alt = float(input("Enter altitude degrees: "))
        az = float(input("Enter azimuth degrees: "))

        # ADD FUNCTIONALITY TO MOVE TELESCOPE HERE
    elif choice == 2: # Point to radec
        ra = input("Enter Ra value: ")
        dec = input("Enter dec value: ")
        C.convert_radec_to_altaz(ra, dec)

        # ADD FUNCTIONALITY TO MOVE TELESCOPE HERE
    elif choice == 3: # Tracking
        code = input("\nEnter the code of the celestial object that you would like to track: ")
        print("\n")

        TM.track_celestial_object(code)
    elif choice == 4: # Rest mode
        # ADD FUNCTIONALITY TO MAKE TELESCOPE ENTER REST MODE
        pass
    elif choice == 5: # Back to main menu, do not check this value
        pass
    else:
        print("Invalid input, please enter a number next to the command you want to execute.")

def configure_settings_functions(choice):
    if choice == 1: # Change Telescope Location
        pass
    elif choice == 2: # Data store location
        pass
    elif choice == 3: # Back to main menu, do not check this value
        pass
    else: print("Invalid input, please enter a number next to the command you want to execute.")

def coordinate_functions(choice):
    if choice == 1: # Convert AltAz to Ra & Dec
        alt = float(input("Enter altitude degrees: "))
        az = float(input("Enter azimuth degrees: "))
        ra, dec = C.convert_altaz_to_radec(alt, az)

        print(f"Altaz converted to ra and dec:  RA: {ra}  DEC: {dec}")
    elif choice == 2: # Convert Ra & Dec to AltAZ
        ra = input("Enter Ra value: ")
        dec = input("Enter dec value: ")
        alt, az = C.convert_radec_to_altaz(ra, dec)

        print(f"radec converted to alt and az:  ALT: {alt}  AZ: {az}")
    elif choice == 3: # Back to main menu, do not check this value
        pass
    else: print("Invalid input, please enter a number next to the command you want to execute.")

def display_sys_data_functions(choice):
    if choice == 1: # Display location
        print("(Latiude, Longitude, Elevation)")
        print(f"IP: {C.ip_get_location_and_elevation()}")
        # print(f"Last Saved: {}")
    elif choice == 2: # Display telescope logs
        FH.display_logs()
    elif choice == 3: # Display commands & descriptions
        print("\nAvailable commands: \n")

        for command, description in COMMAND_DESCRIPTIONS.items():
            print(f"{command}: {description}")
    elif choice == 4: # Back to main menu, do not check this value
        pass
    else: print("Invalid input, please enter a number next to the command you want to execute.")

def __main__():
    b_flag = False

    # Check login details
    while b_flag == False:
        user = input("Enter your username: ")
        password = input("Enter your password: ")

        if (USER == user) & (PASSWORD == password):
            b_flag = True
        else: print("Incorrect login!!!\n")

    print("\n")

    while True:
        display_menu(0) # Display main menu
        choice = int(input("\nEnter your choice: ")) # Input to select menu
        display_menu(choice)

        if choice == 1: # Telescope control
            tc_choice = int(input("\nEnter your choice: "))
            telescope_control_functions(tc_choice)
        elif choice == 2: # Configure settings
            cs_choice = int(input("\nEnter your choice: "))
            configure_settings_functions(cs_choice)
        elif choice == 3: # Coordinate system
            c_choice = int(input("\nEnter your choice: "))
            coordinate_functions(c_choice)
        elif choice == 4: # Display system data
            sd_choice = int(input("\nEnter your choice: "))
            display_sys_data_functions(sd_choice)
        elif choice == 5: # Exit
            exit()
        else:
            print("Invalid input, please enter a number next to the command you want to execute.")
        
        print("\n")

if __name__ == '__main__':
    __main__()