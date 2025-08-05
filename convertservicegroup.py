import re

def normalize_name(name):
    """Replace spaces with hyphens and strip extra characters."""
    return re.sub(r'[^a-zA-Z0-9_\-]', '-', name.strip())

def parse_service_group_config(lines):
    groups = []
    current = {}

    for line in lines:
        line = line.strip()

        if line.startswith("edit"):
            current = {
                "name": re.findall(r'"(.*?)"', line)[0],
                "members": []
            }

        elif line.startswith("set member"):
            members = re.findall(r'"(.*?)"', line)
            current["members"].extend(members)

        elif line.startswith("next"):
            groups.append(current)
            current = {}

    return groups

def convert_to_paloalto(groups):
    output = []
    for grp in groups:
        name = normalize_name(grp["name"])
        member_list = " ".join(grp["members"])
        output.append(f"set service-group {name} members [ {member_list} ]")
    return output

# ====== RUN SCRIPT ======

with open("fortigate_service_group_config.txt", "r") as f:
    lines = f.readlines()

groups = parse_service_group_config(lines)
paloalto_cmds = convert_to_paloalto(groups)

with open("paloalto_service_groups_output.txt", "w") as f:
    for cmd in paloalto_cmds:
        f.write(cmd + "\n")

print("✅ Service group conversion complete.")
print(f"✔️  Groups converted: {len(paloalto_cmds)} (saved to paloalto_service_groups.txt)")
