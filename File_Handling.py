import os
import re
from datetime import datetime

def get_script_path():
    """Returns the directory path of the current script."""
    return os.path.dirname(os.path.abspath(__file__))

def file_exists(file_path):
    """Checks if a file exists and is a regular file."""
    try:
        if os.path.isfile(file_path):
            return True, None
        elif os.path.exists(file_path):
            return False, "Path exists but is not a regular file."
        else:
            return False, "File does not exist."
    except OSError as e:
        return False, str(e)

def is_valid_directory(directory):
    """
    Validates if the given path is a valid, existing directory.
    Checks for empty string, path traversal, and invalid characters.
    """
    directory = directory.strip()
    if not directory:
        return False, "Directory path cannot be empty."
    if re.search(r"(\.\./|\.\.\\)", directory):
        return False, "Directory path cannot contain traversal patterns (../ or ..\\)."
    if re.search(r"[<>*\|]", directory):
        return False, "Directory path contains invalid characters (<>*|)."
    if not os.path.isdir(directory):
        if os.path.exists(directory):
            return False, f"The path '{directory}' exists but is not a directory."
        else:
            return False, f"The directory '{directory}' does not exist."
    return True, None

def write_log(user, command, status, description):
    """
    Writes a log entry to Logs.txt or Errors.txt depending on status.
    """
    now = datetime.now()
    record = f"{now.date()}\t{now.strftime('%H:%M:%S')}\t{user}\t{command}\t{description}"
    log_dir = os.path.join(get_script_path(), "Resources")
    os.makedirs(log_dir, exist_ok=True)
    file_name = "Logs.txt" if status else "Errors.txt"
    append_to_file(os.path.join(log_dir, file_name), record)

def display_logs():
    """
    Displays the contents of Logs.txt and Errors.txt in the terminal.
    """
    log_dir = os.path.join(get_script_path(), 'Resources')
    logs_path = os.path.join(log_dir, 'Logs.txt')
    errors_path = os.path.join(log_dir, 'Errors.txt')

    print("Logs:\n")
    if os.path.exists(logs_path):
        with open(logs_path, 'r') as file:
            print(file.read())
    else:
        print("No logs found.")

    print("\nErrors:\n")
    if os.path.exists(errors_path):
        with open(errors_path, 'r') as file:
            print(file.read())
    else:
        print("No errors found.")

def append_to_file(file_path, content):
    """
    Appends a line of text to the specified file, creating directories if needed.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as file:
            file.write("\n" + content)
    except FileNotFoundError:
        print(f"Failed to load file: {file_path}")
    except PermissionError:
        print(f"Permission denied. Cannot write to: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # Placeholder for future CLI or test code
    pass

if __name__ == '__main__':
    main()