import pandas as pd
import re
import math

# ==== CONFIG ====
fortigate_config_file = "fortigate-config.txt"  # FortiGate config input file
mapping_file = "set-category.xlsx"          # Mapping sheet (Excel or CSV)
output_file = "application_filters.txt"         # Where to store the output

# ==== STEP 1: Read FortiGate Config ====
with open(fortigate_config_file, "r") as f:
    config_data = f.read()

# Find all 'edit "<group name>"' blocks that have set category
group_pattern = re.finditer(
    r'edit\s+"([^"]+)".*?set category ([\d\s]+).*?next',
    config_data,
    re.S
)

# ==== STEP 2: Read Mapping Sheet ====
df = pd.read_excel(mapping_file)  # or pd.read_csv(mapping_file)

# Ensure required columns exist
expected_cols = ['cat ID', 'Category', 'Subcategory', 'Technology']
for col in expected_cols:
    if col not in df.columns:
        raise ValueError(f"Missing column in mapping file: {col}")

# ==== STEP 3: Process Each Group ====
all_output_lines = []

for match in group_pattern:
    group_name = match.group(1)  # e.g. Clone of Avalon_TL_APP
    category_numbers = [int(num) for num in match.group(2).split()]

    matching_df = df[df['cat ID'].isin(category_numbers)]

    all_output_lines.append(f"### {group_name} ###")  # Header for grouping

    for _, row in matching_df.iterrows():
        for col in ['Category', 'Subcategory', 'Technology']:
            value = row[col]

            # Skip if value is NaN or "NA"
            if pd.isna(value) or str(value).strip().upper() == "NA":
                continue

            value = str(value).strip()
            line = f"set application-filter {value}_filter {col} {value}"

            # Skip if line contains nan_filter
            if "nan_filter" in line.lower():
                continue

            all_output_lines.append(line)

    all_output_lines.append("")  # Blank line between groups

# ==== STEP 4: Save Output ====
with open(output_file, "w") as f:
    f.write("\n".join(all_output_lines))

print(f"[+] Generated {len(all_output_lines)} lines (including headers).")
print(f"[+] Saved to {output_file}")
