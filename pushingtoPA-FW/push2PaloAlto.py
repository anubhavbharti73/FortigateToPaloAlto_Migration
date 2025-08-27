from getpass import getpass
import os
import logging
from datetime import datetime
from netmiko import ConnectHandler, NetMikoAuthenticationException, NetMikoTimeoutException

def push_function(username, password, hostip): 

    # 🔹 Directories
    CONFIG_DIR = "config"
    LOG_DIR = "logs"

    # Create logs folder if not exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # 🔹 Setup Logging
    log_filename = os.path.join(LOG_DIR, f"palo_config_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # 🔹 Device credentials
    firewall = {
        "device_type": "paloalto_panos",
        "host": hostip,    
        "username": username,      
        "password": password, 
        "fast_cli": True,  # 🔹 Makes Netmiko run faster
    }

    # 🔹 Load config files
    try:
        config_files = sorted([f for f in os.listdir(CONFIG_DIR) if os.path.isfile(os.path.join(CONFIG_DIR, f))])
        if not config_files:
            print(f"❌ No config files found in '{CONFIG_DIR}'")
            exit(1)
    except FileNotFoundError:
        print(f"❌ Config directory '{CONFIG_DIR}' not found.")
        exit(1)

    logging.info(f"Found {len(config_files)} config files: {config_files}")

    # 🔹 Connect to firewall
    try:
        logging.info(f"Connecting to {firewall['host']}...")
        net_connect = ConnectHandler(**firewall)
        print(f"✅ Connected to {firewall['host']}")
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        logging.error(f"Connection failed: {str(e)}")
        print(f"❌ Connection failed: {str(e)}")
        exit(1)

    # 🔹 Process each config file
    for file in config_files:
        file_path = os.path.join(CONFIG_DIR, file)
        print(f"\n📄 Processing file: {file}")
        logging.info(f"Processing file: {file}")

        try:
            with open(file_path) as f:
                commands = f.read().splitlines()
        except Exception as e:
            logging.error(f"Error reading {file}: {str(e)}")
            print(f"❌ Error reading {file}")
            continue

        logging.info(f"Loaded {len(commands)} commands from {file}")

        # 🔹 Push all commands in bulk
        try:
            output = net_connect.send_config_set(commands)
            if "Invalid" in output or "error" in output.lower():
                logging.error(f"One or more commands failed in {file} | Output: {output.strip()}")
                print(f"⚠️ Errors detected in {file}, skipping commit.")
                continue
            else:
                logging.info(f"Commands from {file} pushed successfully")
                print(f"✅ Commands from {file} pushed successfully")
        except Exception as e:
            logging.error(f"Error pushing commands from {file}: {str(e)}")
            print(f"❌ Error pushing commands from {file}")
            continue

        # 🔹 Commit changes with longer timeout
        print(f"💾 Committing changes for {file}...")
        try:
            commit_output = net_connect.send_command(
                "commit",
                expect_string=r"admin@PA-VM>",  # Wait for Palo Alto prompt
                read_timeout=120       # Wait up to 2 minutes
            )
            logging.info(f"Commit successful for {file}: {commit_output.strip()}")
            print(f"✅ Commit successful for {file}")
        except Exception as e:
            logging.error(f"Commit failed for {file}: {str(e)}")
            print(f"❌ Commit failed for {file}")

    # 🔹 Disconnect
    net_connect.disconnect()
    print(f"\n🔒 Disconnected. Log saved to {log_filename}")


def main():
    hostip = input("Enter your host-ip: ")
    username = input("Enter your username: ")
    password = getpass("Enter your password: ")
    push_function(username, password, hostip)
    exit1 = input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
    