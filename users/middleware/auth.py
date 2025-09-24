import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os 

load_dotenv()

# --- Configuration (should use environment variables in production) ---
# Make SECRET_KEY lookup lazy to avoid import-time failures in CLI/tests
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
try:
    TOKEN_EXPIRY_HOURS = int(os.getenv("TOKEN_EXPIRY_HOURS", "24"))
except ValueError:
    TOKEN_EXPIRY_HOURS = 24

def _get_secret_key():
    key = os.getenv("SECRET_KEY")
    if not key:
        raise RuntimeError("SECRET_KEY is not set. Define SECRET_KEY in your environment or .env file.")
    return key

def generate_jwt(user_id):
    """
    Generate a JWT token for a given user ID.
    The token contains the user_id and an expiry time.
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    secret = _get_secret_key()
    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt(token):
    """
    Verify a JWT token and return the payload if valid.
    Returns (payload, None) if valid, (None, error_message) if not.
    """
    try:
        secret = _get_secret_key()
        decoded = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
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

    # Normalize potential bytes values from legacy storage or calling code
    stored_hash = user.get('password')
    if isinstance(stored_hash, bytes):
        try:
            stored_hash = stored_hash.decode('utf-8')
        except Exception:
            return None, 'Stored password hash is not valid UTF-8'

    # Reject missing/blank stored hash early
    if not stored_hash or (isinstance(stored_hash, str) and stored_hash.strip() == ''):
        return None, 'Password not set for user'

    if isinstance(password, bytes):
        try:
            password = password.decode('utf-8')
        except Exception:
            return None, 'Password provided is not valid UTF-8'

    try:
        # Preferred: verify via Werkzeug hash
        if not check_password_hash(stored_hash, password):
            return None, "Invalid password"
    except Exception as exc:
        # Fallback for legacy records with plaintext passwords or unknown hash methods
        message = str(exc)
        if 'Invalid hash method' in message or 'hash is not a valid' in message:
            if stored_hash == password:
                # Accept legacy plaintext match; encourage migration elsewhere
                pass
            else:
                return None, 'Invalid password'
        else:
            return None, 'Password verification error'

    token = generate_jwt(user['id'])          # Generate JWT
    return token, None