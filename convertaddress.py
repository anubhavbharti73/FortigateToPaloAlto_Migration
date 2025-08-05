import ipaddress
import re

def convert_mask_to_cidr(ip, mask):
    """Convert IP + netmask to CIDR."""
    try:
        return str(ipaddress.IPv4Network(f"{ip}/{mask}", strict=False))
    except Exception:
        return f"{ip}/{mask}"  # fallback

def normalize_name(name):
    """Normalize names to be Palo Alto CLI friendly."""
    name = name.lower()
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    return name

def parse_fortigate_config(config_lines):
    entries = []
    current = {}

    for line in config_lines:
        line = line.strip()
        if line.startswith("edit"):
            current = {"name": re.findall(r'"(.*?)"', line)[0]}
        elif line.startswith("set type"):
            current["type"] = line.split()[-1]
        elif line.startswith("set fqdn"):
            current["fqdn"] = line.split()[-1].strip('"')
        elif line.startswith("set subnet"):
            parts = line.split()
            current["ip"] = parts[2]
            current["mask"] = parts[3]
        elif line.startswith("next"):
            entries.append(current)
            current = {}

    return entries

def convert_to_paloalto(entries):
    output = []
    for entry in entries:
        name = normalize_name(entry.get("name", "unnamed"))
        if entry.get("type") == "fqdn":
            fqdn = entry.get("fqdn", name)
            output.append(f'set address {name} fqdn {fqdn}')
        elif "ip" in entry and "mask" in entry:
            cidr = convert_mask_to_cidr(entry["ip"], entry["mask"])
            output.append(f'set address {name} ip-netmask {cidr}')
        else:
            output.append(f'# Skipped: {entry}')
    return output

# Example: reading from file
with open("fortigate_address_config.txt", "r") as f:
    lines = f.readlines()

entries = parse_fortigate_config(lines)
palo_cmds = convert_to_paloalto(entries)

# Save to output file
with open("paloalto_address_output.txt", "w") as f:
    for cmd in palo_cmds:
        f.write(cmd + "\n")

print("✅ Conversion complete. Output saved to paloalto_output.txt")
