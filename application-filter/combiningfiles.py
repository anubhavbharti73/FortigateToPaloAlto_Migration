file1 = "appgroup_B.txt"
file2 = "appgroup_A.txt"
output_file = "final_output-generated.txt"

with open(file1, "r", encoding="utf-8") as f1, open(file2, "r", encoding="utf-8") as f2:
    content1 = f1.read()
    content2 = f2.read()

# Combine and remove any duplicate blank lines
combined_content = (content1.strip() + "\n" + content2.strip()).strip()

with open(output_file, "w", encoding="utf-8") as out:
    out.write(combined_content + "\n")

print(f"[+] Combined '{file1}' and '{file2}' into '{output_file}'")
