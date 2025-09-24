import requests
import json
import sys
import logging
from datetime import datetime
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

# === LOAD ENV VARIABLES ===
load_dotenv()  # Loads variables from .env file into environment

# === LOGGING CONFIGURATION ===
LOG_FILE = "scm_push.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# === CONFIGURATION ===
CLIENT_ID = os.getenv("SCM_CLIENT_ID")
CLIENT_SECRET = os.getenv("SCM_CLIENT_SECRET")
TSG_ID = os.getenv("SCM_TSG_ID")

if not CLIENT_ID or not CLIENT_SECRET or not TSG_ID:
    logging.error("Missing SCM_CLIENT_ID, SCM_CLIENT_SECRET, or SCM_TSG_ID in .env file.")
    sys.exit("❌ Missing environment variables. Check logs for details.")

TOKEN_URL = "https://auth.apps.paloaltonetworks.com/oauth2/access_token"
ADDRESS_API = "https://api.strata.paloaltonetworks.com/config/objects/v1/addresses"

# === FUNCTION TO GET ACCESS TOKEN ===
def get_access_token():
    try:
        payload = {
            "grant_type": "client_credentials",
            "scope": f"tsg_id:{TSG_ID}"
        }

        response = requests.post(
            TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
        )

        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            if token:
                logging.info("Successfully fetched access token.")
                print(token)
                return token
            else:
                logging.error("Access token missing in response: %s", token_data)
                sys.exit("❌ Token fetch failed. Check logs for details.")
        else:
            logging.error("Failed to fetch token: %s", response.text)
            sys.exit(f"❌ Failed to get token ({response.status_code}). Check logs.")

    except requests.exceptions.RequestException as e:
        logging.exception("RequestException while fetching token.")
        sys.exit("❌ Token request failed. Check logs for details.")

# === FUNCTION TO PUSH ADDRESS OBJECT ===
def push_address(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # address_payload = {
    #     "name": "Sample-Address-API",
    #     "type": "ip-netmask",
    #     "value": "192.168.50.10/32",
    #     "description": "Pushed via SCM API from Python script",
    #     "folder": "Shared"
    # }

    address_payload = {
        "name": "Sample-Address-API",
        "folder": "Shared",
        "ip_netmask": "192.168.50.10/32",  
        "description": "Pushed via SCM API from Python script"
    }

    # address_payload = {
    #     "name": "Sample-Address-API",
    #     "folder": "",
    #     "ip_netmask": {
    #         "value": "192.168.50.10/32"
    #     },
    #     "description": "Pushed via SCM API from Python script"
    # }



    try:
        response = requests.post(ADDRESS_API, headers=headers, data=json.dumps(address_payload))

        if response.status_code in [200, 201]:
            logging.info("Address object '%s' created successfully.", address_payload["name"])
            print("✅ Address object created successfully!")
            print(json.dumps(response.json(), indent=2))
        else:
            logging.error("Failed to create address object '%s': %s", address_payload["name"], response.text)
            print(f"❌ Failed to create address object: {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        logging.exception("RequestException while pushing address object.")
        sys.exit("❌ Address push failed. Check logs for details.")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    logging.info("==== SCM Push Started at %s ====", datetime.now())
    token = get_access_token()
    push_address(token)
    logging.info("==== SCM Push Completed ====")
