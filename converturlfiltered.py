import re

def normalize_url(url, url_type):
    if url_type == "wildcard":
        url = url.replace("*", ".*")
        if not url.startswith(".*"):
            url = ".*" + url
        return url
    return url

def parse_urlfilter_config(lines):
    filters = []
    current_filter = None
    in_entries = False
    current_entries = []

    for line in lines:
        line = line.strip()

        if line.startswith("edit") and not in_entries:
            current_filter = {"name": "", "urls": []}

        elif line.startswith("set name") and current_filter is not None:
            current_filter["name"] = re.findall(r'"(.*?)"', line)[0]

        elif line == "config entries":
            in_entries = True
            current_entries = []

        elif line == "end" and in_entries:
            current_filter["urls"] = current_entries
            filters.append(current_filter)
            in_entries = False

        elif in_entries:
            if line.startswith("edit"):
                current_entry = {"url": None, "type": "plain", "action": "allow"}
            elif line.startswith("set url"):
                match = re.findall(r'"(.*?)"', line)
                if match:
                    current_entry["url"] = match[0]
            elif line.startswith("set type"):
                match = re.findall(r'"(.*?)"', line)
                if match:
                    current_entry["type"] = match[0]
            elif line.startswith("set action"):
                match = re.findall(r'"(.*?)"', line)
                if match:
                    current_entry["action"] = match[0]
            elif line.startswith("next"):
                current_entries.append(current_entry)

    return filters

def convert_to_paloalto_url_cmds(filters):
    output_cmds = []
    skipped = []

    for f in filters:
        profile_name = f'A-PUN_RMZ_UTM_{f["name"]}'
        urls = []

        for entry in f["urls"]:
            url = entry.get("url")
            url_type = entry.get("type", "plain")

            if not url:
                skipped.append(f'{profile_name} - missing URL')
                continue

            try:
                normalized = normalize_url(url, url_type)
                urls.append(normalized)
            except Exception as e:
                skipped.append(f'{profile_name} - {url} - {str(e)}')

        if urls:
            output_cmds.append(f'set profiles custom-url-category "{profile_name}" type "URL List"')
            output_cmds.append(f'set profiles custom-url-category "{profile_name}" list [ {" ".join(urls)} ]')
        else:
            skipped.append(f'{profile_name} - no valid URLs')

    return output_cmds, skipped

# ===== MAIN LOGIC =====

with open("fortigate_urlfiltered_config.txt", "r") as f:
    lines = f.readlines()

filters = parse_urlfilter_config(lines)
palo_cmds, skipped_entries = convert_to_paloalto_url_cmds(filters)

# Write Palo Alto commands
with open("paloalto_urlfiltered_output.txt", "w") as f:
    for cmd in palo_cmds:
        f.write(cmd + "\n")

# Write skipped entries
with open("skipped_url_entries.txt", "w") as f:
    for s in skipped_entries:
        f.write(s + "\n")

print("✅ Conversion complete.")
print(f"✔️ Converted profiles: {len(filters) - len(skipped_entries)}")
print(f"❌ Skipped items: {len(skipped_entries)} (see skipped_url_entries.txt)")