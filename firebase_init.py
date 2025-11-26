import os
import json
import firebase_admin
from firebase_admin import credentials

raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not raw_json:
    raise Exception("FIREBASE_SERVICE_ACCOUNT_JSON missing")

# parse JSON directly — DO NOT MODIFY STRING
cred_dict = json.loads(raw_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(cred_dict))

print("✅ Firebase Admin initialized")
