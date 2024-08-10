import os, sys

# Custom libraries
import Calculations as C, File_Handling as FH


def display_menu():
    print("\n")

    print("*******************************")
    print("   Radio Telescope Control     ")
    print("*******************************")
    print("1. Telescope Control")
    print("2. Data Management")
    print("3. Coordinate Systems")
    print("4. cd")
    print("5. Display Logs")
    print("6. Exit")

    print("\n")

def display_command_descriptions(command_descriptions):
    for key, value in command_descriptions.items():
        print(f"{key}: {value}")

def __main__():
    command_descriptions = {
        "telescope_control": "Control telescope movement and position.",
        "data_management": "Manage data related to observations and telescope operations.",
        "coordinate_systems": "Work with different coordinate systems for astronomical objects.",
        "change_directory": "Change the current working directory.",
        "display_logs": "Display system logs and records.",
        "exit": "Terminate the program.",
        "azimuth_control": "Control the telescope's horizontal movement.",
        "elevation_control": "Control the telescope's vertical movement.",
        "tracking": "Continuously adjust the telescope's position to follow a celestial object.",
        "rest_mode": "Park the telescope in a safe position.",
        "reporting": "Generate reports based on collected data.",
        "file_path": "Specify the location for saving data files.",
        "set_location": "Define the telescope's geographic location.",
        "celestial_to_altaz_conversion": "Convert from celestial coordinates (ra and dec) to altaz degrees.",
        "altaz_to_celestial_conversion": "Convert from alt az degrees to celestial coordinates (ra and dec)."
    }

    user = input("Enter your username: ") # Get username for logging

    while True:
        display_menu() # Display the main menu
        # Get user input for main menu choice
        choice = input("Enter your choice: ")
        print("\n")
        if choice == '1':
            print("Telescope Control Menu:")
            print("1. Azimuth Control")
            print("2. Elevation Control")
            print("3. Tracking")
            print("4. Rest Mode")
            print("\n")
            tc_choice = input("Enter your choice: ")
            if tc_choice == "1":
                print(command_descriptions["azimuth_control"])
                FH.write_log(user,"Telescope control","Azimuth control selected")
                # add azimuth control functionality
            elif tc_choice == "2":
                print(command_descriptions["elevation_control"])
                FH.write_log(user, "Telescope Control", "Elevation Control selected")
                # add elevation control functionality
            elif tc_choice == "3":
                print(command_descriptions["tracking"])
                FH.write_log(user, "Telescope Control", "Tracking selected")
                # add tracking functionality
            elif tc_choice == "4":
                print(command_descriptions["rest_mode"])
                FH.write_log(user, "Telescope Control", "Rest Mode selected")
                # add rest mode functionality
            else:
                print("Invalid choice")

        elif choice == '2':
            print("Data Management Menu:")
            print("1. Reporting")
            print("2. File Path")
            print("\n")
            dm_choice = input("Enter your choice: ")
            if dm_choice == "1":
                print(command_descriptions["reporting"])
                FH.write_log(user, "Data Management", "Reporting selected")
                # add reporting functionality
            elif dm_choice == "2":
                print(command_descriptions["file_path"])
                FH.write_log(user, "Data Management", "File Path selected")
                # add file path functionality
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
                print(command_descriptions["set_location"])
                FH.write_log(user, "Coordinate Systems", "Set Location selected")
                # add set locations functionality
            elif cs_choice == "2":
                print(command_descriptions["celestial_to_altaz_conversion"], '\n')
                ra = float(input("Enter the right ascesion (ra) value: "))
                dec = float(input("Enter the declination (dec) value: "))

                alt_deg, az_deg = C.celestial_to_altaz(ra, dec)

                print(f"Current Location: {C.get_location_and_elevation()}")
                print(f"Altitude: {alt_deg:.2f} degrees, Azimuth: {az_deg:.2f} degrees")
                FH.write_log(user, "Coordinate Systems", f"Celestial to Altaz Conversion: {ra}, {dec} -> {alt_deg:.2f}, {az_deg:.2f}")
            elif cs_choice == "3":
                print(command_descriptions["altaz_to_celestial_conversion"])
                alt = float(input("Enter the altitude (alt) value: "))
                az = float(input("Enter the azimuth (az) value: "))

                ra, dec = C.altaz_to_celestial(alt, az)

                print(f"Current Location: {C.get_location_and_elevation()}")
                print(f"Celestial Coordinates (ra, dec): ({ra}, {dec})")
                FH.write_log(user, "Coordinate Systems", f"Altaz to Celestial Conversion: {alt}, {az} -> {ra:.2f}, {dec:.2f}")
            else:
                print("Invalid choice")

        elif choice == '4':
            print(command_descriptions["change_directory"])
            directory = input("Enter new directory: ")
            try:
              os.chdir(directory)
              FH.write_log(user, "Change Directory", f"Changed directory to: {os.getcwd()}")
              print(f"Changed directory to: {os.getcwd()}")
            except OSError:
              print("Directory change failed.")
              FH.write_log(user, "Change Directory", f"Directory change failed: {directory}")

        elif choice == "5":
            print(command_descriptions["display_logs"], '\n')
            FH.write_log(user, "Display Logs", "Accessed system logs")
            FH.display_logs()
        elif choice == "6":
            print(command_descriptions["exit"])
            FH.write_log(user,"Exit","Terminated the program")
            exit()
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    __main__()