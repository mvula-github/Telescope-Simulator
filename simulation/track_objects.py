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

def _parse_ra_dec(ra_dec: str):
    try:
        if not ra_dec:
            return None, None
        ra_str, dec_str = ra_dec.split(',')
        ra = float(ra_str.strip())
        dec = float(dec_str.strip())
        return ra, dec
    except Exception:
        return None, None

def create_object(user_id: str, name: str, description: str, ra_dec: str, ned_code: str):
    if objects_collection is None:
        print("Database not initialized.")
        return
    ra_val, dec_val = _parse_ra_dec(ra_dec)
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
    if ra_val is not None and dec_val is not None:
        obj["ra"] = ra_val
        obj["dec"] = dec_val
    try:
        objects_collection.insert_one(obj)
        print(f"Astronomical object '{name}' created.")
    except PyMongoError as e:
        print(f"Error creating object: {e}")

def list_objects(user_id: str = None, role: str = 'operator', show_all: bool = False):
    if objects_collection is None:
        print("Database not initialized.")
        return []
    try:
        # If show_all is True, return all objects regardless of role
        if show_all:
            query = {}
        else:
            query = {} if role == 'admin' else {"user_id": user_id}
        
        objs = list(objects_collection.find(query))
        if not objs:
            print("No astronomical objects found.")
            return []
        for obj in objs:
            print(f"Name: {obj['name']}, Description: {obj['description']}, RA/Dec: {obj.get('ra_dec','')}, NED Code: {obj['ned_code']}, User ID: {obj.get('user_id', 'N/A')}")
        return objs
    except PyMongoError as e:
        print(f"Error listing objects: {e}")
        return []

def update_object(name: str, description: str = None, ra_dec: str = None, ned_code: str = None, user_id: str = None, role: str = 'operator'):
    if objects_collection is None:
        print("Database not initialized.")
        return
    update_data = {"updated_at": datetime.now()}
    if description is not None:
        update_data["description"] = description
    if ra_dec is not None:
        update_data["ra_dec"] = ra_dec
        ra_val, dec_val = _parse_ra_dec(ra_dec)
        if ra_val is not None and dec_val is not None:
            update_data["ra"] = ra_val
            update_data["dec"] = dec_val
    if ned_code is not None:
        update_data["ned_code"] = ned_code
    try:
        filter_query = {"name": name}
        if role != 'admin' and user_id is not None:
            filter_query["user_id"] = user_id
        result = objects_collection.update_one(filter_query, {"$set": update_data})
        if result.matched_count:
            print(f"Astronomical object '{name}' updated.")
        else:
            print(f"No object found with name '{name}'.")
    except PyMongoError as e:
        print(f"Error updating object: {e}")

def delete_object(name: str, user_id: str = None, role: str = 'operator'):
    if objects_collection is None:
        print("Database not initialized.")
        return
    try:
        filter_query = {"name": name}
        if role != 'admin' and user_id is not None:
            filter_query["user_id"] = user_id
        result = objects_collection.delete_one(filter_query)
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