import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os 

load_dotenv()

# --- Configuration (should use environment variables in production) ---
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
try:
    TOKEN_EXPIRY_HOURS = int(os.getenv("TOKEN_EXPIRY_HOURS", "24"))
except ValueError:
    TOKEN_EXPIRY_HOURS = 24

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Define SECRET_KEY in your environment or .env file.")

def generate_jwt(user_id):
    """
    Generate a JWT token for a given user ID.
    The token contains the user_id and an expiry time.
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt(token):
    """
    Verify a JWT token and return the payload if valid.
    Returns (payload, None) if valid, (None, error_message) if not.
    """
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return decoded, None
    except jwt.ExpiredSignatureError:
        return None, 'Token expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'

def token_required(f):
    """
    Flask route decorator to enforce JWT authentication.
    Checks for a valid JWT in the Authorization header.
    If valid, passes user_id to the route handler.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')  # Get the Authorization header
        if not auth_header:
            return jsonify({'message': 'Token missing'}), 401

        try:
            token = auth_header.split(" ")[1]  # Extract token from "Bearer <token>"
        except IndexError:
            return jsonify({'message': 'Token format invalid'}), 401

        decoded, error = verify_jwt(token)    # Verify the token
        if error:
            return jsonify({'message': error}), 401

        user_id = decoded['user_id']          # Extract user_id from token
        return f(user_id, *args, **kwargs)    # Pass user_id to the route

    return decorated

def authenticate_user(username, password, getUsername):
    """
    Validates user credentials.
    - getUsername(username) should return a user dict with 'id' and 'password'.
    - Checks if user exists and password is correct.
    - Returns (token, None) if successful, (None, error_message) otherwise.
    """
    user = getUsername(username)           # Fetch user by username
    if not user:
        return None, "User not found"

    if not check_password_hash(user['password'], password):  # Verify password
        return None, "Invalid password"

    token = generate_jwt(user['id'])          # Generate JWT
    return token, None