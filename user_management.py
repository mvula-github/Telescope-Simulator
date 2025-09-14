import getpass
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import os
import File_Handling as FH
from werkzeug.security import generate_password_hash


# Load .env
load_dotenv()

# MongoDB setup for Users collection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'celestiCodeServerDB')
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db['users']
except PyMongoError as e:
    print(f"Error: Failed to connect to MongoDB for Users collection: {e}")
    users_collection = None

# Initialize MongoDB
try:
    FH.init_mongodb()
except RuntimeError as e:
    print(f"Error: {e}")
    users_collection = None

# Create a new user
def create_user():
    if not users_collection:
        print("Database not initialized.")
        return
    try:
        name = input("Enter name: ")
        surname = input("Enter surname: ")
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        role = input("Enter role (admin/operator): ").lower()
        if role not in ['admin', 'operator']:
            print("Invalid role. Must be 'admin' or 'operator'.")
            return
        hashed_password = generate_password_hash(password)
        user_data = {
            'name': name,
            'surname': surname,
            'username': username,
            'password': hashed_password,  # Use 'password' field
            'role': role,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        users_collection.insert_one(user_data)
        print(f"User '{username}' created successfully.")
        FH.write_log("admin", "Create User", "success", f"Created user '{username}' with role '{role}'")
    except PyMongoError as e:
        print(f"Error creating user: {e}")
        FH.write_log("admin", "Create User", "error", f"Failed to create user: {e}")

# List all users
def list_users():
    if not users_collection:
        print("Database not initialized.")
        return
    try:
        users = users_collection.find()
        print("\nUsers:")
        for user in users:
            print(f"Username: {user['username']}, Name: {user['name']} {user['surname']}, Role: {user['role']}")
        FH.write_log("admin", "List Users", "success", "Listed all users")
    except PyMongoError as e:
        print(f"Error listing users: {e}")
        FH.write_log("admin", "List Users", "error", f"Failed to list users: {e}")

# Update an existing user
def update_user():
    if not users_collection:
        print("Database not initialized.")
        return
    try:
        username = input("Enter username to update: ")
        user = users_collection.find_one({"username": username})
        if not user:
            print(f"User '{username}' not found.")
            return
        print(f"Current details: Name: {user['name']}, Surname: {user['surname']}, Role: {user['role']}")
        
        name = input("Enter new name (press enter to keep current): ") or user['name']
        surname = input("Enter new surname (press enter to keep current): ") or user['surname']
        role = input("Enter new role (admin/operator, press enter to keep current): ").lower() or user['role']
        if role and role not in ['admin', 'operator']:
            print("Invalid role. Must be 'admin' or 'operator'.")
            return
        password = getpass.getpass("Enter new password (press enter to keep current): ")
        update_data = {
            'name': name,
            'surname': surname,
            'role': role,
            'updated_at': datetime.now()
        }
        if password:
            update_data['password'] = generate_password_hash(password)  # Use 'password' field
        users_collection.update_one({"username": username}, {"$set": update_data})
        print(f"User '{username}' updated successfully.")
        FH.write_log("admin", "Update User", "success", f"Updated user '{username}'")
    except PyMongoError as e:
        print(f"Error updating user: {e}")
        FH.write_log("admin", "Update User", "error", f"Failed to update user: {e}")

# Delete an existing user
def delete_user():
    if not users_collection:
        print("Database not initialized.")
        return
    try:
        username = input("Enter username to delete: ")
        user = users_collection.find_one({"username": username})
        if not user:
            print(f"User '{username}' not found.")
            return
        users_collection.delete_one({"username": username})
        print(f"User '{username}' deleted successfully.")
        FH.write_log("admin", "Delete User", "success", f"Deleted user '{username}'")
    except PyMongoError as e:
        print(f"Error deleting user: {e}")
        FH.write_log("admin", "Delete User", "error", f"Failed to delete user: {e}")
