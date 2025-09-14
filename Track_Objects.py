from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME', 'celestiCodeServerDB')

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    objects_collection = db['astronomical_objects']
except PyMongoError as e:
    print(f"Error: Failed to connect to MongoDB for Astronomical Objects: {e}")
    objects_collection = None

def create_object(user_id: str, name: str, description: str, ra_dec: str, ned_code: str):
    if objects_collection is None:
        print("Database not initialized.")
        return
    obj = {
        "user_id": user_id,
        "name": name,
        "description": description,
        "ra_dec": ra_dec,
        "ned_code": ned_code,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "tracking": False
    }
    try:
        objects_collection.insert_one(obj)
        print(f"Astronomical object '{name}' created.")
    except PyMongoError as e:
        print(f"Error creating object: {e}")

def list_objects(user_id: str):
    if objects_collection is None:
        print("Database not initialized.")
        return
    try:
        objs = list(objects_collection.find({"user_id": user_id}))
        if not objs:
            print("No astronomical objects found.")
            return
        for obj in objs:
            print(f"Name: {obj['name']}, Description: {obj['description']}, RA/Dec: {obj['ra_dec']}, NED Code: {obj['ned_code']}, User ID: {obj['user_id']}")
    except PyMongoError as e:
        print(f"Error listing objects: {e}")

def update_object(name: str, description: str = None, ra_dec: str = None, ned_code: str = None):
    if objects_collection is None:
        print("Database not initialized.")
        return
    update_data = {"updated_at": datetime.now()}
    if description is not None:
        update_data["description"] = description
    if ra_dec is not None:
        update_data["ra_dec"] = ra_dec
    if ned_code is not None:
        update_data["ned_code"] = ned_code
    try:
        result = objects_collection.update_one({"name": name}, {"$set": update_data})
        if result.matched_count:
            print(f"Astronomical object '{name}' updated.")
        else:
            print(f"No object found with name '{name}'.")
    except PyMongoError as e:
        print(f"Error updating object: {e}")

def delete_object(name: str):
    if objects_collection is None:
        print("Database not initialized.")
        return
    try:
        result = objects_collection.delete_one({"name": name})
        if result.deleted_count:
            print(f"Astronomical object '{name}' deleted.")
        else:
            print(f"No object found with name '{name}'.")
    except PyMongoError as e:
        print(f"Error deleting object: {e}")

def track_object(user_id: str, object_id: str):
    if objects_collection is None:
        print("Database not initialized.")
        return
    try:
        obj = objects_collection.find_one({"user_id": user_id, "_id": object_id})
        if obj:
            objects_collection.update_one({"user_id": user_id, "_id": object_id}, {"$set": {"tracking": True}})
            print(f"Object '{obj['name']}' is now being tracked.")
        else:
            print(f"Object with ID '{object_id}' not found.")
    except PyMongoError as e:
        print(f"Error tracking object: {e}")