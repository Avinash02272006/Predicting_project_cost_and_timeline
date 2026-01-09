
import requests

API_URL = "http://127.0.0.1:8000"

def test_auth():
    print("Testing Registration...")
    try:
        reg = requests.post(f"{API_URL}/register", json={
            "username": "testuser_debug",
            "email": "test@debug.com",
            "password": "pass"
        })
        print(f"Register Status: {reg.status_code}")
        print(f"Register Response: {reg.text}")
    except Exception as e:
        print(f"Register Failed: {e}")

    print("\nTesting Login...")
    try:
        login = requests.post(f"{API_URL}/token", data={
            "username": "testuser_debug",
            "password": "pass"
        })
        print(f"Login Status: {login.status_code}")
        print(f"Login Response: {login.text}")
    except Exception as e:
        print(f"Login Failed: {e}")

if __name__ == "__main__":
    test_auth()
