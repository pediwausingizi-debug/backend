import os
import json
import firebase_admin
from firebase_admin import credentials

raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not raw:
    raise Exception("❌ FIREBASE_SERVICE_ACCOUNT_JSON missing!")

# Step 1 — Convert REAL newlines inside env into \n so JSON becomes valid
normalized = raw.replace("\r", "").replace("\n", "\\n")

# Step 2 — Now decode JSON properly
try:
    fixed = normalized.encode("utf-8").decode("unicode_escape")
    cred_dict = json.loads(fixed)
except Exception as e:
    print("🔥 ERROR parsing JSON")
    print("RAW:", raw[:300], "...")
    raise e

# Step 3 — Init Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

print("✅ Firebase Admin initialized")
