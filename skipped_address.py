def extract_skipped_lines(file_path, output_path=None):
    skipped_lines = []

    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('# Skipped:'):
                skipped_lines.append(line.strip())

    if output_path:
        with open(output_path, 'w') as out_file:
            for skipped in skipped_lines:
                out_file.write(skipped + '\n')
    else:
        for skipped in skipped_lines:
            print(skipped)

# Example usage:
# Provide path to your file
input_file = 'NEW_paloalto_address_output.txt'
# Optional: Provide path to save output, or leave as None to just print
output_file = 'skipped_address_entries.txt'

extract_skipped_lines(input_file, output_file)
