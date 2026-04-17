from google import genai

# Paste your Gemini API key here (and keep it a secret this time!)
api_key = "your-api-key"

# Setup the connection to Gemini
# The SDK will use the key provided here
client = genai.Client(api_key=api_key)

print("Attempting to connect to Gemini...")

try:
    # Send a test message
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents="Hello! Are you working?"
    )
    
    # If this works, your key is valid!
    print("\n✅ SUCCESS! Connection established.")
    print("Response from AI:", response.text)

except Exception as e:
    # If this fails, the key is broken/invalid
    print("\n❌ FAILED. The key is rejected.")
    print("Error details:", e)
