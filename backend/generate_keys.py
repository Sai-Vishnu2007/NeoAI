import time
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from jose import jwt

# 1. Generate the RSA Keys (The Lock and Key)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
).decode('utf-8')

pem_public = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode('utf-8')

# 2. Create the Token for your PC (The Passport)
# This token is set to last for 10 years so you don't have to keep regenerating it.
payload = {
    "sub": "vishnu_admin",
    "scope": "voice_client",
    "iat": int(time.time()),
    "exp": int(time.time()) + (10 * 365 * 24 * 60 * 60)
}
token = jwt.encode(payload, pem_private, algorithm="RS256")

print("\n" + "="*50)
print("STEP A: ADD THESE TO YOUR SERVER'S .env FILE")
print("="*50)
print(f'JWT_PRIVATE_KEY="{pem_private}"')
print(f'\nJWT_PUBLIC_KEY="{pem_public}"')

print("\n" + "="*50)
print("STEP B: ADD THIS TO YOUR LOCAL PC config.json")
print("="*50)
print(f'"jwt_token": "{token}"')
print("="*50 + "\n")
