from pymongo import MongoClient
import pandas as pd

# Step 1: Connect to MongoDB
uri = "mongodb+srv://python:raspi123@sensors.g0oav.mongodb.net/?retryWrites=true&w=majority&appName=sensors"
client = MongoClient(uri)
db = client['sensor_data']  # Replace with your database name
sensor_collection = db['sensor_readings'] 

# Check MongoDB connection before proceeding
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit()

# Step 3: Fetch all documents
documents = list(sensor_collection.find())

# Step 4: Convert to DataFrame
df = pd.DataFrame(documents)

# Step 5 (Optional): Remove MongoDB’s _id field
if '_id' in df.columns:
    df = df.drop(columns=['_id'])

# Step 6: Save to CSV
df.to_csv('/home/ani/Documents/Pfiles/Raspi/sensor_data.csv', index=False)
print("CSV file saved as sensor_data.csv")
