import os, sys, re
from datetime import datetime

def get_script_path():
    return os.path.dirname(os.path.realpath(__file__))

def file_exists(file_path):
    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return True, None  # File exists and is regular
        else:
            return False, "File does not exist or is not a regular file"  # File doesn't exist or is a directory
    except OSError as e:
        # Handle OSError and return the error message
        return False, str(e)

# Test if a directory is valid and exists
def is_valid_directory(dir):
    dir = dir.strip() # Input Sanitization (Remove leading and trailing whitespace)

    # Check if path is an empty string
    if not dir:
        return False, "Directory path cannot be empty."

    # Path Traversal Pattern Check (Attempts to access parent directories)
    if re.search(r"(\.\./|\.\.\\)", dir):  # Platform-agnostic
        return False, "Directory path cannot contain traversal patterns (../ or ..\\)."

    # Other Suspicious Patterns
    if re.search(r"[<>*\|]", dir):
        return False, "Directory path contains invalid characters (<>*|)."

    if not os.path.isdir(dir):
        if os.path.exists(dir):  # Check if it exists but is not a directory
            return False, f"The path '{dir}' exists but is not a directory."
        else:
            return False, f"The directory '{dir}' does not exist."

    return True, None  # No error message since the directory is valid

def write_log():
    time = datetime.now().strftime("%H:%M:%S")
    date = datetime.now().date()

def __main__():
    pass
if __name__ == '__main__':
    __main__()