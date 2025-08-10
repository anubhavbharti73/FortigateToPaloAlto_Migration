input_file = "paloalto_addrgrp_output.txt"
output_file = "paloalto_shortaddrgrp_output.txt"

def shorten_name(name):
    if len(name) > 20:
        return name[:10] + '-' + name[-9:]
    return name

with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    for line in infile:
        stripped_line = line.strip()

        # Skip comments
        if stripped_line.startswith("# Skipped") or not stripped_line:
            # outfile.write(line)
            continue

        if stripped_line.startswith("set address-group"):
            parts = stripped_line.split()
            if len(parts) < 4:
                # Not a valid address line
                outfile.write(line)
                continue

            original_name = parts[2]
            new_name = shorten_name(original_name)

            # Replace only the address name
            updated_line = line.replace(f"address-group {original_name}", f"address-group {new_name}")
            outfile.write(updated_line)

            # Add description if name was shortened
            if new_name != original_name:
                description_line = f'set address-group {new_name} description {original_name}\n'
                outfile.write(description_line)
        else:
            outfile.write(line)
