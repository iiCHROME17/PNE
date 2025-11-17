import requests
import json

# Test direct connection
print("Testing Ollama connection...")
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:3b",
        "prompt": "Say hello in 5 words.",
        "stream": False
    },
    timeout=30
)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"✓ Success! Response: {result.get('response', '')}")
else:
    print(f"✗ Error: {response.text}")