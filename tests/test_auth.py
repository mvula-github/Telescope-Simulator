import unittest
from users.middleware.auth import (
    generate_jwt,
    verify_jwt,
    authenticate_user,
    token_required
)
from werkzeug.security import generate_password_hash
import jwt
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Mock config (should match your auth.py config)
SECRET_KEY = os.getenv("SECRET_KEY") 
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

class TestAuthentication(unittest.TestCase):

    def setUp(self):
        # Test user details
        self.username = "username"
        self.user_id = "user123"
        self.password = "securePassword"
        self.hashed_password = generate_password_hash(self.password)

        # Simulated user database (dictionary)
        self.mock_user_db = {
            self.username: {
                "id": self.user_id,
                "username": self.username,
                "password_hash": self.hashed_password
            }
        }

        # Function to fetch user by username from mock database
        self.getUsername = lambda username: self.mock_user_db.get(username)

    def test_generate_jwt_returns_token(self):
        # Test that generate_jwt returns a string token
        token = generate_jwt(self.user_id)
        self.assertIsInstance(token, str)

    def test_verify_jwt_valid_token(self):
        # Test that a valid token is verified and decoded correctly
        token = generate_jwt(self.user_id)
        decoded, error = verify_jwt(token)
        self.assertIsNone(error)
        self.assertEqual(decoded["user_id"], self.user_id)

    def test_verify_jwt_expired_token(self):
        # Test that an expired token returns the correct error
        payload = {
            'user_id': self.user_id,
            'exp': time.time() - 10  # expired 10 seconds ago
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
        decoded, error = verify_jwt(expired_token)
        self.assertIsNone(decoded)
        self.assertEqual(error, "Token expired")

    def test_authenticate_user_success(self):
        # Test successful authentication returns a token and no error
        token, error = authenticate_user(self.username, self.password, self.username)
        self.assertIsNotNone(token)
        self.assertIsNone(error)

    def test_authenticate_user_wrong_password(self):
        # Test authentication fails with wrong password
        token, error = authenticate_user(self.username, "wrongPassword", self.username)
        self.assertIsNone(token)
        self.assertEqual(error, "Invalid password")

    def test_authenticate_user_unknown_username(self):
        # Test authentication fails with unknown username
        token, error = authenticate_user("unknown", self.password, self.username)
        self.assertIsNone(token)
        self.assertEqual(error, "User not found")


import unittest
from flask import Flask,request, jsonify
from users.middleware.auth import (
    generate_jwt,
    verify_jwt,
    authenticate_user
)
from werkzeug.security import generate_password_hash
import jwt
import time

class TestTokenRequiredDecorator(unittest.TestCase):

    def setUp(self):
        # Create a minimal Flask app for testing
        self.app = Flask(__name__)

        # Protected route for testing
        @self.app.route("/protected")
        @token_required
        def protected_route(user_id):
            return jsonify({"message": f"Hello {user_id}"}), 200

        self.client = self.app.test_client()

        # Create a valid token for user_id "user123"
        self.valid_token = generate_jwt("user123")

    def test_access_without_token(self):
        """Should return 401 when no token is provided"""
        response = self.client.get("/protected")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Token missing", response.get_data(as_text=True))

    def test_access_with_invalid_token(self):
        """Should return 401 when token is invalid"""
        headers = {"Authorization": "Bearer invalidtoken"}
        response = self.client.get("/protected", headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid token", response.get_data(as_text=True))

    def test_access_with_valid_token(self):
        """Should return 200 and correct message when token is valid"""
        headers = {"Authorization": f"Bearer {self.valid_token}"}
        response = self.client.get("/protected", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello user123", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
