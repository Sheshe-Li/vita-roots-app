"""
One-time script: creates Supabase Auth users for all 9 test families
and links them via auth_user_id on the families table.

Run ONCE:  python seed_auth_users.py

Requires:  SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
           The families table must have an auth_user_id uuid column (see SQL below).

SQL to run in Supabase SQL Editor first:
  ALTER TABLE families ADD COLUMN IF NOT EXISTS auth_user_id uuid UNIQUE;
"""

from dotenv import load_dotenv
load_dotenv()

import os
from supabase import create_client

url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_SERVICE_KEY", "")
client = create_client(url, key)

FAMILIES = [
    {"client_number": "VR-002001", "name": "Rivera",          "email": "rivera@vitaroots.app"},
    {"client_number": "VR-002002", "name": "Johnson-Williams", "email": "johnson@vitaroots.app"},
    {"client_number": "VR-002003", "name": "Chen",            "email": "chen@vitaroots.app"},
    {"client_number": "VR-002004", "name": "Okafor",          "email": "okafor@vitaroots.app"},
    {"client_number": "VR-002005", "name": "Washington",      "email": "washington@vitaroots.app"},
    {"client_number": "VR-002006", "name": "Patel",           "email": "patel@vitaroots.app"},
    {"client_number": "VR-002007", "name": "Nguyen",          "email": "nguyen@vitaroots.app"},
    {"client_number": "VR-002008", "name": "Hernandez",       "email": "hernandez@vitaroots.app"},
    {"client_number": "VR-002009", "name": "Thompson",        "email": "thompson@vitaroots.app"},
]
PASSWORD = "VitaRoots2026!"

print("\n=== Seeding Supabase Auth users ===\n")

for f in FAMILIES:
    email = f["email"]
    client_number = f["client_number"]

    # 1. Look up the family row
    fam = client.table("families").select("id, name, auth_user_id").eq("client_number", client_number).execute()
    if not fam.data:
        print(f"  SKIP  {client_number} — family row not found in DB")
        continue

    row = fam.data[0]
    family_id = row["id"]

    if row.get("auth_user_id"):
        print(f"  SKIP  {client_number} ({email}) — already linked to auth_user_id {row['auth_user_id']}")
        continue

    # 2. Create auth user (or get existing)
    try:
        resp = client.auth.admin.create_user({
            "email": email,
            "password": PASSWORD,
            "email_confirm": True,
            "user_metadata": {"family_id": family_id, "client_number": client_number},
        })
        user_id = resp.user.id
        print(f"  CREATE  {email}  →  auth_user_id={user_id}")
    except Exception as exc:
        msg = str(exc)
        if "already been registered" in msg or "already exists" in msg:
            # Get existing user by listing and filtering
            users = client.auth.admin.list_users()
            match = next((u for u in users if u.email == email), None)
            if match:
                user_id = match.id
                print(f"  EXISTS  {email}  →  auth_user_id={user_id}")
            else:
                print(f"  ERROR   {email} exists but couldn't retrieve: {exc}")
                continue
        else:
            print(f"  ERROR   {email}: {exc}")
            continue

    # 3. Link auth user to family row
    client.table("families").update({"auth_user_id": str(user_id)}).eq("id", family_id).execute()
    print(f"          Linked to family {client_number} ({row.get('name', '')})")

print("\nDone. Login credentials:")
print(f"  Passwords:  {PASSWORD}")
for f in FAMILIES:
    print(f"  {f['client_number']:12s}  {f['email']}")
