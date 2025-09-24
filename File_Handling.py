import os
import re
from datetime import datetime
from typing import Tuple, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from tabulate import tabulate
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# MongoDB settings from .env
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'celestiCodeServerDB')

client = None
db = None
collection = None

# Fallback file paths
LOGS_FILE = os.path.join('Resources', 'Logs.txt')
ERRORS_FILE = os.path.join('Resources', 'Errors.txt')

def init_mongodb():
    """Initialize MongoDB connection. Falls back to file logging if unavailable."""
    global client, db, collection
    try:
        client = MongoClient(MONGO_URI)
        client.admin.command('ismaster')  # Test connection
        db = client[DB_NAME]
        collection = db['Logs']
        collection.create_index([('timestamp', -1)], background=True)
        print("MongoDB connected successfully.")
    except (ConnectionFailure, PyMongoError) as e:
        # Fall back to file-based logging
        client = None
        db = None
        collection = None
        print(f"Warning: MongoDB unavailable ({e}). Falling back to file logging at {LOGS_FILE}.")
        # Ensure fallback directory exists
        try:
            os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
            if not os.path.exists(LOGS_FILE):
                with open(LOGS_FILE, 'a', encoding='utf-8') as f:
                    f.write('Date\tTime\tUser\tCommand\tDescription\n')
            if not os.path.exists(ERRORS_FILE):
                with open(ERRORS_FILE, 'a', encoding='utf-8') as f:
                    f.write('Date\tTime\tUser\tCommand\tError Message\n')
        except OSError:
            pass

def get_script_path() -> str:
    """Returns the directory path of the current script."""
    return os.path.dirname(os.path.abspath(__file__))

def file_exists(file_path: str) -> Tuple[bool, Optional[str]]:
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

def is_valid_directory(directory: str) -> Tuple[bool, Optional[str]]:
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

def write_log(user: str, command: str, level: str, description: str):
    """
    Insert log entry to MongoDB Logs collection with level (success, error, warning).
    Raises exception on failure to ensure no silent failures.
    """
    if level not in ('success', 'error', 'warning'):
        raise ValueError(f"Invalid log level: {level}. Must be 'success', 'error', or 'warning'.")
    log_entry = {
        'timestamp': datetime.now(),
        'user': user,
        'command': command,
        'level': level,
        'description': description
    }
    try:
        if collection is not None:
            collection.insert_one(log_entry)
            return
    except PyMongoError as e:
        print(f"Error: Failed to write log to MongoDB: {e}")
        # Fall back to file below

    # Fallback to file-based logging
    try:
        os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        line = f"{date_str}\t{time_str}\t{user}\t{command}\t{description}\n"
        with open(LOGS_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
        if level == 'error':
            with open(ERRORS_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{date_str}\t{time_str}\t{user}\t{command}\t{description}\n")
    except OSError as e:
        print(f"Error: Failed to write fallback log files: {e}")

def display_logs():
    """
    Display logs from MongoDB if available, otherwise from fallback file.
    """
    try:
        if collection is not None:
            logs = list(collection.find().sort('timestamp', -1).limit(100))
            if not logs:
                print("No logs found in MongoDB.")
                return

            # Group logs by level
            levels = {}
            for log in logs:
                level = log['level']
                if level not in levels:
                    levels[level] = []
                levels[level].append([
                    log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    log['user'],
                    log['command'],
                    log['description']
                ])

            # Print logs grouped by level using tabulate
            for level, entries in sorted(levels.items()):
                print(f"\n{level.upper()} Logs:")
                headers = ["Timestamp", "User", "Command", "Description"]
                print(tabulate(entries, headers=headers, tablefmt="github"))
            return
    except PyMongoError as e:
        print(f"Error: Failed to fetch logs from MongoDB: {e}")

    # Fallback to file
    try:
        if not os.path.exists(LOGS_FILE):
            print("No logs available (fallback file missing).")
            return
        with open(LOGS_FILE, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        if len(lines) <= 1:
            print("No logs available in fallback file.")
            return
        # Print last 100 entries excluding header
        header = lines[0]
        entries = lines[1:][-100:]
        print(header)
        for line in entries:
            print(line)
    except OSError as e:
        print(f"Error: Failed to read fallback log file: {e}")

def main():
    init_mongodb()
    write_log("test_user", "Test Command", "success", "Test log entry")
    display_logs()

if __name__ == '__main__':
    main()