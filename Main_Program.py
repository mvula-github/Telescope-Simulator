import os, sys

# Custom libraries
import Calculations as C, File_Handling as FH

def display_menu():
    """Displays the main menu with options for the user."""
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
    """Displays descriptions for available commands."""
    for key, value in command_descriptions.items():
        print(f"{key}: {value}")

def __main__():
    """Main function for the radio telescope control software."""

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
        "coordinate_conversion": "Convert between celestial and Alt/Az coordinates."
    }



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
                # add azimuth control functionality
            elif tc_choice == "2":
                print(command_descriptions["elevation_control"])
                # add elevation control functionality
            elif tc_choice == "3":
                print(command_descriptions["tracking"])
                # add tracking functionality
            elif tc_choice == "4":
                print(command_descriptions["rest_mode"])
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
                # add reporting functionality
            elif dm_choice == "2":
                print(command_descriptions["file_path"])
                # add file path functionality
            else:
                print("Invalid choice")

        elif choice == '3':
            print("Coordinate Systems Menu:")
            print("1. Set Location")
            print("2. Coordinate Conversion")
            print("\n")
            cs_choice = input("Enter your choice: ")
            if cs_choice == "1":
                print(command_descriptions["set_location"])
                # add set locations functionality
            elif cs_choice == "2":
                print(command_descriptions["coordinate_conversion"])
                # add coordinate conversion functionality
            else:
                print("Invalid choice")

        elif choice == '4':
            print(command_descriptions["change_directory"])
            # add change directory functionality
            print("cd action executed")
        elif choice == "5":
            print(command_descriptions["display_logs"], '\n')
            
            FH.display_logs()
        elif choice == "6":
            print(command_descriptions["exit"])
            exit()
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    __main__()