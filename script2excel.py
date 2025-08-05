import re
import pandas as pd

# File path to your input file
input_file = 'Fortigate 7.4.8 application list.txt'
output_file = 'Fortigate_data.xlsx'

# Fields to extract
fields = ['app-name', 'id', 'category', 'protocol', 'technology', 'behavior', 'app_port', 'parent']

# Read full file content
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Split content by empty lines to get each app block
app_blocks = re.split(r'\n\s*\n', content.strip())

records = []

# Process each block
for block in app_blocks:
    record = {}
    for field in fields:
        match = re.search(rf"^{field}:\s*\"?([^\n\"]*)\"?$", block, re.MULTILINE)
        if match:
            record[field] = match.group(1).strip()
        else:
            record[field] = ""  # Set blank if not present
    records.append(record)

# Create DataFrame and export to Excel
df = pd.DataFrame(records)
df.to_excel(output_file, index=False)

# Load the just-written Excel file
df_clean = pd.read_excel(output_file)

# Clean the behavior column if it accidentally contains 'language: ...'
df_clean['behavior'] = df_clean['behavior'].apply(
    lambda x: "" if isinstance(x, str) and x.strip().startswith("language:") else x
)

# Save the cleaned DataFrame back to the same Excel file
df_clean.to_excel(output_file, index=False)

print(f"✅ Cleaned behavior column and saved to '{output_file}'")


print(f"✅ Successfully extracted {len(records)} records to '{output_file}'")
