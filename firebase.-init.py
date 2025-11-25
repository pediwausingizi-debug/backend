import os
import json
import firebase_admin
from firebase_admin import credentials

# Read the JSON from the environment
raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not raw_json:
    raise Exception("FIREBASE_SERVICE_ACCOUNT_JSON is missing!")

# Convert JSON string → Python dict
cred_dict = json.loads(raw_json)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
