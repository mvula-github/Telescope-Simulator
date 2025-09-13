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

def init_mongodb():
    """Initialize MongoDB connection."""
    global client, db, collection
    try:
        client = MongoClient(MONGO_URI)
        client.admin.command('ismaster')  # Test connection
        db = client[DB_NAME]
        collection = db['Logs'] 
        collection.create_index([('timestamp', -1)], background=True)
        print("MongoDB connected successfully.")
    except ConnectionFailure as e:
        print(f"Error: MongoDB connection failed: {e}. Ensure MONGO_URI is correct and MongoDB is accessible.")
        raise RuntimeError(f"MongoDB connection failed: {e}")
    except PyMongoError as e:
        print(f"Error: MongoDB initialization error: {e}")
        raise RuntimeError(f"MongoDB initialization error: {e}")

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
        if collection is None:
            raise RuntimeError("MongoDB not initialized. Cannot write log.")
        collection.insert_one(log_entry)
    except PyMongoError as e:
        print(f"Error: Failed to write log to MongoDB: {e}")
        raise RuntimeError(f"Failed to write log to MongoDB: {e}")

def display_logs():
    """
    Query and display logs from MongoDB, grouped by level.
    """
    try:
        if collection is None:
            raise RuntimeError("MongoDB not initialized. Cannot display logs.")

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

        # Print logs grouped by level
        for level, entries in sorted(levels.items()):
            print(f"\n{level.upper()} Logs:")
            print("-" * 100)
            print(f"{'Timestamp':<20} {'User':<15} {'Command':<20} {'Description':<40}")
            print("-" * 100)

            for entry in entries:
                timestamp, user, command, description = entry
                print(f"{timestamp:<20} {user:<15} {command:<20} {description:<40}")

            print("-" * 100)

    except PyMongoError as e:
        print(f"Error: Failed to fetch logs from MongoDB: {e}")
    except RuntimeError as e:
        print(f"Error: {e}")

def main():
    init_mongodb()
    write_log("test_user", "Test Command", "success", "Test log entry")
    display_logs()

if __name__ == '__main__':
    main()