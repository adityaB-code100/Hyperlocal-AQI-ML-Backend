from pymongo import MongoClient
from atlas import get_mongo_uri


def test_mongodb_connection():
    try:
        # Get MongoDB URI from .env
        mongo_uri = get_mongo_uri()

        print("🔄 Connecting to MongoDB...")

        # Connect
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        client.admin.command("ping")

        print("✅ MongoDB connection successful!")

        # Show databases
        databases = client.list_database_names()

        print("\n📂 Available databases:")
        for db in databases:
            print(f"   - {db}")

        # Select your database
        db = client["AQI_Project"]

        print("\n📁 Collections in AQI_Project:")

        for collection in db.list_collection_names():
            print(f"   - {collection}")

        client.close()

        print("\n✅ Test completed successfully!")

    except Exception as e:
        print("\n❌ MongoDB connection failed!")
        print("Error:", e)


if __name__ == "__main__":
    test_mongodb_connection()