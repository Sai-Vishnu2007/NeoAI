from qdrant_client import QdrantClient

# Connect to the exact port your app uses
client = QdrantClient("http://localhost:6335")

# Obliterate the specific collection
client.delete_collection(collection_name="agent_documents")

print("💥 The B.Tech Zombie has been eradicated from Port 6335.")