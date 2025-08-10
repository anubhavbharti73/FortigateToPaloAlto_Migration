import re

# Files to process
files = ["appgroup_A.txt", "appgroup_B.txt"]

def clean_bracket_list(match):
    items = match.group(1).split()
    cleaned_items = [
        item for item in items
        if item.lower() != "nan" and not item.isdigit()
    ]
    return "[ " + " ".join(cleaned_items) + " ]"

for file_path in files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove 'nan' and numeric IDs inside square brackets
    cleaned_content = re.sub(r"\[([^\]]+)\]", clean_bracket_list, content)

    with open(file_path+"_uodate", "w", encoding="utf-8") as f:
        f.write(cleaned_content)

print("[+] Removed 'nan' and numeric IDs from all bracket lists.")
