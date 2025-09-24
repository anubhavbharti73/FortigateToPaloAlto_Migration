import os
import json
import logging
import sys
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

# ====== CONFIG ======
LOG_FILE = "scm_push.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

CLIENT_ID = os.getenv("SCM_CLIENT_ID")
CLIENT_SECRET = os.getenv("SCM_CLIENT_SECRET")
TSG_ID = os.getenv("SCM_TSG_ID")
REGION = os.getenv("SCM_REGION", "api")  # e.g. api, api.eu, api.sg

if not CLIENT_ID or not CLIENT_SECRET or not TSG_ID:
    logging.error("Missing SCM_CLIENT_ID / SCM_CLIENT_SECRET / SCM_TSG_ID in .env")
    sys.exit("❌ Missing env variables")

BASE_URL = f"https://{REGION}.strata.paloaltonetworks.com"
TOKEN_URL = "https://auth.apps.paloaltonetworks.com/oauth2/access_token"
ADDRESS_API = f"{BASE_URL}/config/objects/v1/addresses"
COMMIT_API = f"{BASE_URL}//config/commit/v1/commits"

# ====== TOKEN ======
def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "scope": f"tsg_id:{TSG_ID}"
    }
    try:
        resp = requests.post(
            TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
        )
        logging.debug("Token response status: %s, body: %s", resp.status_code, resp.text)
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            if token:
                return token
            else:
                logging.error("No access_token in response JSON: %s", resp.json())
                sys.exit("X Token missing")
        else:
            logging.error("Failed token fetch: %s %s", resp.status_code, resp.text)
            sys.exit("X Token fetch failed")
    except Exception as e:
        logging.exception("Exception fetching token")
        sys.exit("X Exception fetching token")

# ====== ADDRESS FUNCTIONS ======
def build_address_payload(addr_type: str, value: str, name: str, folder: str = "Shared", description: str = ""):
    if addr_type not in ["ip_netmask", "ip_range", "fqdn", "ip_wildcard"]:
        raise ValueError("Invalid addr_type")
    return {
        "name": name,
        "folder": folder,
        "description": description,
        addr_type: value
    }

def push_address(access_token, payload: dict):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = json.dumps(payload)
    logging.info("Pushing address payload: %s", body)
    resp = requests.post(ADDRESS_API, headers=headers, data=body)
    logging.info("Response status: %s, body: %s", resp.status_code, resp.text)
    if resp.status_code in (200, 201):
        print(" Address created:", resp.json())
    else:
        print("X Failed to create address object:", resp.status_code, resp.text)
    return resp

def commit_changes(access_token, folders=["Shared"]):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = json.dumps({"folders": folders})
    logging.info("Committing changes for folders: %s", folders)
    resp = requests.post(COMMIT_API, headers=headers, data=body)
    logging.info("Commit response: %s %s", resp.status_code, resp.text)
    if resp.status_code in (200, 201, 202):
        print(" Commit triggered:", resp.json())
    else:
        print("X Commit failed:", resp.status_code, resp.text)

def list_addresses(access_token, folder="Shared"):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"folder": folder}
    resp = requests.get(ADDRESS_API, headers=headers, params=params)
    logging.info("List addresses status: %s, body: %s", resp.status_code, resp.text)
    if resp.status_code == 200:
        data = resp.json()
        addresses = data.get("data", [])
        if not addresses:
            print("! No address objects found.")
        else:
            print(f" Found {len(addresses)} address objects:")
            for addr in addresses:
                print(f"- {addr['name']} ({addr.get('ip_netmask') or addr.get('ip_range') or addr.get('fqdn')})")
    else:
        print(" Failed to list addresses:", resp.status_code, resp.text)

# ====== FOLDER FUNCTIONS ======
FOLDER_API = f"{BASE_URL}/config/setup/v1/folders"

def list_folders(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(FOLDER_API, headers=headers)
    logging.info("List folders status: %s, body: %s", resp.status_code, resp.text)
    if resp.status_code == 200:
        data = resp.json()
        folders = data.get("data", [])
        if not folders:
            print("! No folders found.")
        else:
            print(f" Found {len(folders)} folders:")
            for folder in folders:
                print(f"- {folder['name']}")
    else:
        print("X Failed to list folders:", resp.status_code, resp.text)


# ====== MAIN MENU ======
if __name__ == "__main__":
    logging.info("===== Start at %s =====", datetime.now())
    token = get_access_token()

    print("\n--- Strata Cloud Manager Address Manager ---")
    print("1️.  Push a new address")
    print("2️.  List existing addresses")
    print("3️.  List folders")
    choice = input("Select option (1/2/3): ").strip()

    if choice == "1":
        name = input("Enter Address Name: ").strip()
        addr_type = input("Enter Type (ip_netmask/ip_range/fqdn): ").strip()
        value = input("Enter Value (e.g. 192.168.1.1/32): ").strip()
        folder = input("Enter Folder (default: Shared): ").strip() or "Shared"
        desc = input("Enter Description (optional): ").strip()

        payload = build_address_payload(addr_type, value, name, folder, desc)
        resp = push_address(token, payload)
        if resp.status_code in (200, 201):
            print(" Address successfully created. No commit needed in SCM.")

    elif choice == "2":
        folder = input("Enter Folder to list (default: Shared): ").strip() or "Shared"
        list_addresses(token, folder=folder)
    
    elif choice == "3":
        list_folders(token)

    else:
        print(" Invalid choice")
    logging.info("===== End =====")
