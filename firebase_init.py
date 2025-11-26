import os
import json
import firebase_admin
from firebase_admin import credentials

raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not raw_json:
    raise Exception("❌ FIREBASE_SERVICE_ACCOUNT_JSON is missing")

try:
    # Converts escaped \n sequences into real newlines properly
    fixed_json = raw_json.encode("utf-8").decode("unicode_escape")

    cred_dict = json.loads(fixed_json)

except Exception as e:
    print("🔥 ERROR: Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON")
    print("RAW VALUE:", raw_json[:300], "...")
    raise e

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

print("✅ Firebase Admin initialized successfully")
