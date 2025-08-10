import pandas as pd
import re

# Load Excel mapping (keeping IDs as string)
mapping_df = pd.read_excel("FG-PA-Mapping.xlsx", dtype={'id': str, 'PA Match list': str})

# Clean data
mapping_df['id'] = mapping_df['id'].astype(str).str.strip()
mapping_df['PA Match list'] = (
    mapping_df['PA Match list']
    .astype(str)
    .replace(r'[\r\n]+', ' ', regex=True)
    .str.strip()
)

# Files to process
files = ["appgroup_A.txt", "appgroup_B.txt"]

def replace_ids(match):
    ids = match.group(1).split()
    replaced = []

    for app_id in ids:
        if app_id.isdigit():  # Only check numeric IDs
            row = mapping_df[mapping_df['id'] == app_id]
            if not row.empty:
                replaced.append(row.iloc[0]['PA Match list'])
            else:
                replaced.append(app_id)  # Keep original if no match
        else:
            replaced.append(app_id)  # Keep non-digit strings unchanged

    return "[ " + " ".join(replaced) + " ]"

for file_path in files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Apply replacement
    new_content = re.sub(r"\[([^\]]+)\]", replace_ids, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

print("[+] Conversion completed for both files.")


