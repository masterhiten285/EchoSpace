import requests
import time

BASE_URL = "http://127.0.0.1:5000"

print("1. Creating session...")
res = requests.post(f"{BASE_URL}/create_session", json={
    "username": "TestUser_123",
    "duration": 30
})
data = res.json()
print("Session Response:", data)
token = data.get("token")

# Add token header to all subsequent requests
headers = {"X-Session-Token": token} if token else {}

print("\n2. Getting current messages in 'Academic Stress'...")
res = requests.get(f"{BASE_URL}/get_messages/Academic%20Stress", headers=headers)
print("Messages:", res.json())

print("\n3. Sending a new message...")
res = requests.post(f"{BASE_URL}/send_message", json={
    "username": "TestUser_123",
    "room": "Academic Stress",
    "message": "Hello from testing script!"
}, headers=headers)
print("Send Response:", res.json())

time.sleep(1)

print("\n4. Getting messages again...")
res = requests.get(f"{BASE_URL}/get_messages/Academic%20Stress", headers=headers)
print("Updated Messages:", res.json())
