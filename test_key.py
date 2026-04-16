from openai import OpenAI

# This is the exact key you shared
api_key = "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"

# Setup the connection to Groq
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key
)

print("Attempting to connect to Groq...")

try:
    # Send a test message
    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[
            {"role": "user", "content": "Hello! Are you working?"}
        ]
    )
    
    # If this works, your key is valid!
    print("\n✅ SUCCESS! Connection established.")
    print("Response from AI:", response.choices[0].message.content)

except Exception as e:
    # If this fails, the key is broken/invalid
    print("\n❌ FAILED. The key is rejected.")
    print("Error details:", e)