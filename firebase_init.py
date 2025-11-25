import os
import json
import firebase_admin
from firebase_admin import credentials


raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not raw_json:
    raise Exception("❌ FIREBASE_SERVICE_ACCOUNT_JSON missing!")

# STEP 1 — Normalize broken newlines from Railway
# Convert real newlines inside the JSON into \n so JSON becomes valid
fixed = (
    raw_json.replace("\r\n", "\\n")
            .replace("\n", "\\n")
            .replace("\\\\n", "\\n")
)

# STEP 2 — Try parsing safely
try:
    cred_dict = json.loads(fixed)
except Exception as e:
    print("❌ Still invalid JSON, dumping raw for debugging:")
    print(raw_json[:300], "...")  
    raise e

# STEP 3 — Initialize Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
