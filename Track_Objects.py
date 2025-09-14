from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'celestiCodeServerDB')

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    objects_collection = db['astronomical_objects']
except PyMongoError as e:
    print(f"Error: Failed to connect to MongoDB for Astronomical Objects: {e}")
    objects_collection = None

def create_object(name: str, description: str, ra_dec: str, ned_code: str):
    if not objects_collection:
        print("Database not initialized.")
        return
    obj = {
        "name": name,
        "description": description,
        "ra_dec": ra_dec,
        "ned_code": ned_code,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    try:
        objects_collection.insert_one(obj)
        print(f"Astronomical object '{name}' created.")
    except PyMongoError as e:
        print(f"Error creating object: {e}")

def list_objects():
    if not objects_collection:
        print("Database not initialized.")
        return
    try:
        objs = list(objects_collection.find())
        if not objs:
            print("No astronomical objects found.")
            return
        for obj in objs:
            print(f"Name: {obj['name']}, Description: {obj['description']}, RA/Dec: {obj['ra_dec']}, NED Code: {obj['ned_code']}")
    except PyMongoError as e:
        print(f"Error listing objects: {e}")

def update_object(name: str, description: str = None, ra_dec: str = None, ned_code: str = None):
    if not objects_collection:
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
    if not objects_collection:
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