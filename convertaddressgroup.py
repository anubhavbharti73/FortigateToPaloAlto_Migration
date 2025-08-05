import re

def normalize_name(name):
    """Normalize name to Palo Alto friendly format."""
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)  # replace invalid chars
    return name.strip('_')

def parse_addrgrp_config(config_lines):
    groups = []
    current = {}

    for line in config_lines:
        line = line.strip()
        if line.startswith("edit"):
            current = {"name": re.findall(r'"(.*?)"', line)[0], "members": []}
        elif line.startswith("set member"):
            members = re.findall(r'"(.*?)"', line)
            current["members"].extend(members)
        elif line.startswith("next"):
            groups.append(current)
            current = {}

    return groups

def convert_to_paloalto(groups):
    output = []
    for group in groups:
        name = normalize_name(group.get("name", "unnamed"))
        members = group.get("members", [])
        member_str = " ".join(members)
        output.append(f"set address-group {name} static [ {member_str} ]")
    return output

# Example usage
with open("fortigate_addressGroup_config.txt", "r") as f:
    config_lines = f.readlines()

groups = parse_addrgrp_config(config_lines)
palo_cmds = convert_to_paloalto(groups)

# Write to output
with open("paloalto_addrgrp_output.txt", "w") as f:
    for cmd in palo_cmds:
        f.write(cmd + "\n")

print("✅ Address group conversion complete. Output saved to paloalto_addrgrp.txt")
