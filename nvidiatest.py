import requests

# Replace with your actual key (but seriously, regenerate it soon!)
API_KEY = "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"
URL = "https://integrate.api.nvidia.com/v1/models"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

print("Pinging NVIDIA servers...")
response = requests.get(URL, headers=headers)

if response.status_code == 200:
    print("✅ SUCCESS! Your API key is active.\n")
    print("Available Models:")
    
    # Parse the JSON and print just the model names
    models_data = response.json().get("data", [])
    for model in models_data:
        print(f" - {model['id']}")
else:
    print(f"❌ ERROR {response.status_code}: Your key might be invalid or expired.")
    print(response.text)