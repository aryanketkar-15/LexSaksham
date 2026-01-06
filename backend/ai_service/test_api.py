# scripts/test_api.py
import requests

url = "http://127.0.0.1:5000/analyze"
data = {"text": "The Service Provider shall indemnify and hold harmless the Client against all claims."}

response = requests.post(url, json=data)
print(response.json())