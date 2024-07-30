import os, sys

# Global variables
#COMMAND_LIST = ["gd", "rest"]
#COMMAND_DESCRIPTIONS = ["Get current working directory", "Telescope rest mode"]

#def check_command():
   # pass



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



def __main__():
    """Main function for the radio telescope control software."""
    while True:
        display_menu() # Display the main menu
        # Get user input for main menu choice
        choice = input("Enter your choice: ")
        
        if choice == '1':
            print("\n")
            print("Telescope Control Menu:")
            print("1. Azimuth Control")
            print("2. Elevation Control")
            print("3. Tracking")
            print("4. Rest Mode")
            print("\n")
            tc_choice = input("Enter your choice: ")
            if tc_choice == "1":
                print("Azimuth control action executed")
            elif tc_choice == "2":
                print("Elevation control action executed")
            elif tc_choice == "3":
                print("Tracking action executed")
            elif tc_choice == "4":
                print("Rest mode action executed")
            else:
                print("Invalid choice")

        elif choice == '2':
            print("Data Management Menu:")
            print("1. Reporting")
            print("2. File Path")
            dm_choice = input("Enter your choice: ")
            if dm_choice == "1":
                print("Reporting action executed")
            elif dm_choice == "2":
                print("File path action executed")
            else:
                print("Invalid choice")

        elif choice == '3':
            print("Coordinate Systems Menu:")
            print("1. Set Location")
            print("2. Coordinate Conversion")
            cs_choice = input("Enter your choice: ")
            if cs_choice == "1":
                print("Set location action executed")
            elif cs_choice == "2":
                print("Coordinate conversion action executed")
            else:
                print("Invalid choice")

        elif choice == '4':
            print("cd action executed")
        elif choice == "5":
            print("Display logs action executed")
        elif choice == "6":
            exit()

        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    __main__()
    
