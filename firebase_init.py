import os
import json
import firebase_admin
from firebase_admin import credentials

raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not raw_json:
    raise Exception("FIREBASE_SERVICE_ACCOUNT_JSON is missing!")

try:
    # 1️⃣ Try to load JSON normally
    try:
        raw_json = raw_json.replace('\\n', '\n')
        cred_dict = json.loads(raw_json)

    except json.JSONDecodeError:
        # 2️⃣ Fix common formatting issues (Railway often strips escapes)
        fixed_json = raw_json.replace("\\n", "\n")
        cred_dict = json.loads(fixed_json)

except Exception as e:
    print("🔥 ERROR: Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON")
    print("RAW VALUE:", raw_json[:200], "...")
    raise e

# 3️⃣ Initialize Firebase
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
    except Exception as e:
        print("🔥 ERROR initializing Firebase:", e)
        raise e
