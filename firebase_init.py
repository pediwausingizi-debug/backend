import os
import json
import firebase_admin
from firebase_admin import credentials

raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not raw:
    raise Exception("❌ FIREBASE_SERVICE_ACCOUNT_JSON missing!")

# Try plain JSON first
try:
    cred_dict = json.loads(raw)
except:
    # Railway usually escapes everything → fix it
    try:
        fixed = raw.encode("utf-8").decode("unicode_escape")
        cred_dict = json.loads(fixed)
    except Exception as e:
        print("🔥 Could not parse Firebase JSON!")
        print("RAW:", raw[:300], "...")
        raise e

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

print("✅ Firebase Admin initialized")
