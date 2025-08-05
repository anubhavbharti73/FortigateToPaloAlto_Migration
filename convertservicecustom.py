import re

def normalize_port_entry(protocol, port_range):
    return f"{protocol}_{port_range}"

def parse_fortigate_service_custom(lines):
    services = []
    skipped = []
    current = {}

    for line in lines:
        line = line.strip()

        if line.startswith("edit"):
            current = {
                "name": re.findall(r'"(.*?)"', line)[0],
                "tcp": [],
                "udp": [],
                "skip": False,
                "has_valid_ports": False
            }

        elif line.startswith("set tcp-portrange"):
            ports = line.split("set tcp-portrange")[1].strip().split()
            current["tcp"].extend(ports)
            current["has_valid_ports"] = True

        elif line.startswith("set udp-portrange"):
            ports = line.split("set udp-portrange")[1].strip().split()
            current["udp"].extend(ports)
            current["has_valid_ports"] = True

        elif re.match(r"set protocol (IP|ICMP)$", line):
            current["skip"] = True

        elif "protocol-number" in line or "unset icmptype" in line:
            current["skip"] = True

        elif line.startswith("next"):
            if current["skip"] or not current["has_valid_ports"]:
                skipped.append(current["name"])
            else:
                services.append(current)
            current = {}

    return services, skipped

def convert_to_paloalto_service_groups(services):
    output = []
    for svc in services:
        members = []
        for tcp in svc["tcp"]:
            members.append(normalize_port_entry("tcp", tcp))
        for udp in svc["udp"]:
            members.append(normalize_port_entry("udp", udp))
        member_str = " ".join(members)
        output.append(f'set service-group {svc["name"]} members [ {member_str} ]')
    return output

# ======== RUN SCRIPT ========

with open("fortigate_service_custom_config.txt", "r") as f:
    lines = f.readlines()

services, skipped = parse_fortigate_service_custom(lines)
paloalto_cmds = convert_to_paloalto_service_groups(services)

with open("paloalto_service_custom_output.txt", "w") as f:
    for cmd in paloalto_cmds:
        f.write(cmd + "\n")

with open("skipped_service_custom.txt", "w") as f:
    for name in skipped:
        f.write(name + "\n")

print("✅ Fixed conversion complete.")
print(f"✔️  Converted services: {len(paloalto_cmds)}")
print(f"⚠️  Skipped entries: {len(skipped)} (check skipped_service_custom.txt)")
