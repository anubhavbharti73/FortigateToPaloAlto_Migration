import pandas as pd
import re

# ==== CONFIG ====
fortigate_config_file = "6. application list"
mapping_file = "set-category.xlsx"
output_a_file = "appgroup_A.txt"
output_b_file = "appgroup_B.txt"
skipped_file = "skipped_entries.txt"

# ==== Load Mapping Sheet ====
df_map = pd.read_excel(mapping_file)
expected_cols = ['cat ID', 'Category', 'Subcategory', 'Technology']
for col in expected_cols:
    if col not in df_map.columns:
        raise ValueError(f"Missing column in mapping file: {col}")

# ==== Read FortiGate Config ====
with open(fortigate_config_file, "r") as f:
    config_text = f.read()

# ==== Match each "edit <name>" block ====
group_pattern = re.finditer(
    r'edit\s+"([^"]+)"(.*?)\n\s*end',
    config_text,
    re.S
)

a_lines = []
b_lines = []
skipped_entries = []

for grp in group_pattern:
    group_name = grp.group(1).strip()
    block = grp.group(2)

    # Match "edit <number>" blocks inside config entries
    entries = re.finditer(
        r'edit\s+\d+(.*?)(?=next)',
        block,
        re.S
    )

    a_members = []
    b_members = []

    for entry in entries:
        entry_block = entry.group(1)

        # Extract app IDs
        app_match = re.search(r'set application\s+([\d\s]+)', entry_block)
        app_ids = app_match.group(1).split() if app_match else []

        # Extract category IDs
        cat_match = re.search(r'set category\s+([\d\s]+)', entry_block)
        cat_ids = cat_match.group(1).split() if cat_match else []

        # Check action pass
        if re.search(r'set action\s+pass', entry_block):
            a_members.extend(app_ids)
        else:
            b_members.extend(app_ids)
            if cat_ids:
                match_df = df_map[df_map['cat ID'].isin([int(x) for x in cat_ids])]
                for _, row in match_df.iterrows():
                    for col in ['Category', 'Subcategory', 'Technology']:
                        val = str(row[col]).strip()
                        if pd.isna(val) or val.upper() == "NA" or val == "":
                            skipped_entries.append(f"{group_name} | catID {row['cat ID']} | {col}")
                            continue
                        fname = f"{val}_filter"
                        if "nan_filter" in fname.lower():
                            skipped_entries.append(f"{group_name} | catID {row['cat ID']} | {col}")
                            continue
                        b_members.append(fname)

    if a_members:
        a_lines.append(f'set application-group "A-{group_name}" members [ {" ".join(a_members)} ]')
    if b_members:
        b_lines.append(f'set application-group "B-{group_name}" members [ {" ".join(b_members)} ]')

# ==== Save Outputs ====
with open(output_a_file, "w") as fa:
    fa.write("\n".join(a_lines))
with open(output_b_file, "w") as fb:
    fb.write("\n".join(b_lines))
with open(skipped_file, "w") as fs:
    fs.write("\n".join(skipped_entries))

print(f"[+] A group file: {output_a_file} ({len(a_lines)} groups)")
print(f"[+] B group file: {output_b_file} ({len(b_lines)} groups)")
print(f"[+] Skipped entries file: {skipped_file} ({len(skipped_entries)} skipped)")

import re

input_file = "appgroup_B.txt"

with open(input_file, "r") as f:
    lines = f.readlines()

with open(input_file, "w") as f:
    for line in lines:
        match = re.search(r'(set application-group\s+"[^"]+"\s+members)\s+\[(.*)\]', line)
        if match:
            prefix = match.group(1)
            members = match.group(2).split()

            # Separate strings and numbers
            strings = [m for m in members if not m.isdigit()]
            numbers = [m for m in members if m.isdigit()]

            # Combine with strings first, numbers later, both sorted
            new_members = sorted(strings) + sorted(numbers, key=int)

            f.write(f"{prefix} [ {' '.join(new_members)} ]\n")
        else:
            f.write(line)

