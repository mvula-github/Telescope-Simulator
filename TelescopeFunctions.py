import os, sys

# Gui libraries
import tkinter as tk 
from tkinter import filedialog 

# Get current working directory
def get_working_directory():
    script_directory = os.path.dirname(os.path.abspath(__file__))

    return script_directory

# Create a 'Data' folder if it does not yet exist
def create_folder(name, location):
    data_directory = os.path.join(location, name)
    os.makedirs(data_directory, exist_ok = True)

    return data_directory

# Select a save location
def get_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window

    # Ask if the user wants to browse or enter manually
    choice = input("Choose how to provide the directory path:\n1. Browse\n2. Enter manually\nYour choice (1 or 2): ")

    if choice == '1':
        directory = filedialog.askdirectory(title = "Select a directory")
    elif choice == '2':
        directory = input("Enter the directory path: ")
    else:
        print("Invalid choice. Exiting...")
        return None

    # Basic validation to ensure it's a valid path
    if not os.path.isdir(directory):
        print("Invalid directory. Exiting...")
        return None

    return directory

def __main__():
    # Select save location
    save_location = get_directory()
    print(save_location)

    # Get current working directory
    script_directory = get_working_directory()
    print("Working directory: ", script_directory)

    # Create a 'Data' folder to store observed data into text files
    data_directory = create_folder('Data', script_directory)

if __name__ == '__main__':
    __main__()