import requests
import json

url = "http://localhost:10000/webhook"

with open("test_payload.json", "r") as file:
    payload = json.load(file)

headers = {"Content-Type": "application/json"}
response = requests.post(url, json=payload, headers=headers)

print("Status Code:", response.status_code)
