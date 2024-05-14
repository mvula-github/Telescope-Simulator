import os, sys # Standard system libraries

sys.path.append(os.getcwd()) # Set working directory

# Import custom libraries
import TelescopeFunctions as TF

def __main__():
    file_to_save = TF.get_save_location()

    if file_to_save != None:
        with open(file_to_save, 'w') as f:
            f.write("This is the content to save\n")

        print("File saved to:", file_to_save)