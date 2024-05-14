# Gui libraries
import tkinter as tk 
from tkinter import filedialog 

# Select a save location
def get_save_location():
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window

    save_location = filedialog.asksaveasfilename(defaultextension = ".txt")

    # If the user cancels, save_location will be an empty string
    if not save_location:
        return None  

    return save_location

def __main__():
    # Select save location
    file_to_save = get_save_location()

    if file_to_save != None:
        with open(file_to_save, 'w') as f:
            f.write("This is the content to save\n")

        print("File saved to:", file_to_save)

if __name__ == '__main__':
    __main__()