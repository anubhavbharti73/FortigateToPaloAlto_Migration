import os
import json
import logging
import sys
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# ====== LOAD ENV ======
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
REGION = os.getenv("SCM_REGION", "api")

if not CLIENT_ID or not CLIENT_SECRET or not TSG_ID:
    logging.error("Missing SCM_CLIENT_ID / SCM_CLIENT_SECRET / SCM_TSG_ID in .env")
    sys.exit("❌ Missing env variables")

BASE_URL = f"https://{REGION}.strata.paloaltonetworks.com"
TOKEN_URL = "https://auth.apps.paloaltonetworks.com/oauth2/access_token"

# ====== ENDPOINTS (Official SCM API) ======
ENDPOINTS = {
    "address": {
        "create": f"{BASE_URL}/config/objects/v1/addresses",
        "list": f"{BASE_URL}/config/objects/v1/addresses"
    },
    "application": {
        "create": f"{BASE_URL}/config/objects/v1/applications",
        "list": f"{BASE_URL}/config/objects/v1/applications"
    },
    "service": {
        "create": f"{BASE_URL}/config/objects/v1/services",
        "list": f"{BASE_URL}/config/objects/v1/services"
    },
    "application_filter": {
        "create": f"{BASE_URL}/config/objects/v1/application-filters",
        "list": f"{BASE_URL}/config/objects/v1/application-filters"
    },
    "dynamic_user_group": {
        "create": f"{BASE_URL}/config/objects/v1/dynamic-user-groups",
        "list": f"{BASE_URL}/config/objects/v1/dynamic-user-groups"
    },
    "region": {
        "create": f"{BASE_URL}/config/objects/v1/regions",
        "list": f"{BASE_URL}/config/objects/v1/regions"
    },
    "folder": {
        "list": f"{BASE_URL}/config/setup/v1/folders"
    }
}

# ====== TOKEN ======
def get_access_token():
    payload = {"grant_type": "client_credentials", "scope": f"tsg_id:{TSG_ID}"}
    try:
        resp = requests.post(
            TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
        )
        logging.debug("Token response: %s %s", resp.status_code, resp.text)
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            if token:
                return token
            logging.error("No access_token in response: %s", resp.json())
            sys.exit("X Token missing")
        logging.error("Failed token fetch: %s %s", resp.status_code, resp.text)
        sys.exit("X Token fetch failed")
    except Exception:
        logging.exception("Exception fetching token")
        sys.exit("X Exception fetching token")

# ====== GENERIC FUNCTIONS ======
def push_object(token, url, payload):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    logging.info("POST %s | %s | %s", url, resp.status_code, resp.text)
    if resp.status_code in (200, 201):
        print("✅ Object created successfully:", resp.json())
    else:
        print("❌ Failed to create object:", resp.status_code, resp.text)

def list_object(token, url):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    logging.info("GET %s | %s | %s", url, resp.status_code, resp.text)
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        if not data:
            print("! No objects found.")
        else:
            for obj in data:
                print(f"- {obj.get('name')}")
    else:
        print("❌ Failed to list objects:", resp.status_code, resp.text)

# ====== OBJECT CREATION FUNCTIONS ======
def create_address(token):
    name = input("Enter Address Name: ").strip()
    addr_type = input("Enter Type (ip_netmask/ip_range/fqdn/ip_wildcard): ").strip()
    value = input("Enter Value: ").strip()
    folder = input("Enter Folder (default: All): ").strip() or "All"
    desc = input("Enter Description (optional): ").strip()
    payload = {"name": name, "folder": folder, "description": desc, addr_type: value}
    push_object(token, ENDPOINTS["address"]["create"], payload)

def create_application(token):
    print("Creating a new Application object...")
    name = input("Enter Application Name: ").strip()
    folder = input("Enter Folder (default: All): ").strip() or "All"
    category = input("Enter Category[business-systems/collaboration/general-internet/media/networking/saas] (required): ").strip()
    subcategory = input("Enter Subcategory (required): ").strip()
    technology = input("Enter Technology (required, e.g., tcp, udp, ssl): ").strip()
    risk = input("Enter Risk (required, 1-5): ").strip()
    description = input("Enter Description (optional): ").strip()
    tags_input = input("Enter comma-separated Tags (optional): ").strip()
    tags = [t.strip() for t in tags_input.split(",")] if tags_input else []

    payload = {
        "name": name,
        "folder": folder,
        "category": category,
        "subcategory": subcategory,
        "technology": technology,
        "risk": int(risk),
        "description": description,
        "tags": tags
    }

    push_object(token, ENDPOINTS["application"]["create"], payload)


def create_service(token):
    name = input("Enter Service Name: ").strip()
    folder = input("Enter Folder (default: All): ").strip() or "All"
    protocol = input("Enter Protocol (tcp/udp/both): ").strip()
    port = input("Enter Port or Port Range: ").strip()
    payload = {"name": name, "folder": folder, "protocol": protocol, "port": port}
    push_object(token, ENDPOINTS["service"]["create"], payload)

def create_application_filter(token):
    name = input("Enter Application Filter Name: ").strip()
    folder = input("Enter Folder (default: All): ").strip() or "All"
    applications = input("Enter comma-separated application names: ").strip().split(",")
    payload = {"name": name, "folder": folder, "applications": [app.strip() for app in applications]}
    push_object(token, ENDPOINTS["application_filter"]["create"], payload)

def create_dynamic_user_group(token):
    name = input("Enter Dynamic User Group Name: ").strip()
    folder = input("Enter Folder (default: All): ").strip() or "All"
    query = input("Enter dynamic user group query: ").strip()
    payload = {"name": name, "folder": folder, "query": query}
    push_object(token, ENDPOINTS["dynamic_user_group"]["create"], payload)

def create_region(token):
    name = input("Enter Region Name: ").strip()
    folder = input("Enter Folder (default: All): ").strip() or "All"
    payload = {"name": name, "folder": folder}
    push_object(token, ENDPOINTS["region"]["create"], payload)

# ====== OBJECT LIST FUNCTIONS ======
def list_addresses(token):
    folder = input("Enter Folder to list (default: All): ").strip() or "All"
    url = f"{ENDPOINTS['address']['list']}?folder={folder}"
    list_object(token, url)

def list_applications(token):
    # list_object(token, ENDPOINTS["application"]["list"])
    folder = input("Enter Folder to list applications (default: All): ").strip() or "All"
    url = f"{ENDPOINTS['application']['list']}?folder={folder}"
    list_object(token, url)

def list_services(token):
    # list_object(token, ENDPOINTS["service"]["list"])
    folder = input("Enter Folder to list Services (default: All): ").strip() or "All"
    url = f"{ENDPOINTS['service']['list']}?folder={folder}"
    list_object(token, url)

def list_application_filters(token):
    # list_object(token, ENDPOINTS["application_filter"]["list"])
    folder = input("Enter Folder to list Application Filter (default: All): ").strip() or "All"
    url = f"{ENDPOINTS['application_filter']['list']}?folder={folder}"
    list_object(token, url)

def list_dynamic_user_groups(token):
    #list_object(token, ENDPOINTS["dynamic_user_group"]["list"])
    folder = input("Enter Folder to list Dynamic User Group (default: All): ").strip() or "All"
    url = f"{ENDPOINTS['dynamic_user_group']['list']}?folder={folder}"
    list_object(token, url)

def list_regions(token):
    # list_object(token, ENDPOINTS["region"]["list"])
    folder = input("Enter Folder to list Regions (default: All): ").strip() or "All"
    url = f"{ENDPOINTS['region']['list']}?folder={folder}"
    list_object(token, url)

def list_folders(token):
    # list_object(token, ENDPOINTS["folder"]["list"])
    folder = input("Enter Folder to list Folders (default: All): ").strip() or "All"
    url = f"{ENDPOINTS['folder']['list']}?folder={folder}"
    list_object(token, url)

# ====== MAIN MENU ======
def main_menu():
    token = get_access_token()
    while True:
        print("\n--- Strata Cloud Manager ---")
        print("1. Create Object")
        print("2. List Object")
        print("0. Exit")
        main_choice = input("Select option: ").strip()

        if main_choice == "1":
            print("\n--- Create Menu ---")
            print("1. Address")
            print("2. Application")
            print("3. Service")
            print("4. Application Filter")
            print("5. Dynamic User Group")
            print("6. Region")
            choice = input("Select object to create: ").strip()
            if choice == "1": create_address(token)
            elif choice == "2": create_application(token)
            elif choice == "3": create_service(token)
            elif choice == "4": create_application_filter(token)
            elif choice == "5": create_dynamic_user_group(token)
            elif choice == "6": create_region(token)
            else: print("Invalid choice.")

        elif main_choice == "2":
            print("\n--- List Menu ---")
            print("1. Address")
            print("2. Folder")
            print("3. Application")
            print("4. Service")
            print("5. Application Filter")
            print("6. Dynamic User Group")
            print("7. Region")
            choice = input("Select object to list: ").strip()
            if choice == "1": list_addresses(token)
            elif choice == "2": list_folders(token)
            elif choice == "3": list_applications(token)
            elif choice == "4": list_services(token)
            elif choice == "5": list_application_filters(token)
            elif choice == "6": list_dynamic_user_groups(token)
            elif choice == "7": list_regions(token)
            else: print("Invalid choice.")

        elif main_choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    logging.info("===== Start =====")
    main_menu()
    logging.info("===== End =====")
