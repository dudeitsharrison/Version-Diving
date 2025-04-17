# Read the file
with open('src/main.py', 'r') as file:
    lines = file.readlines()

# Find the line index to fix
line_to_fix = None
for i, line in enumerate(lines):
    if 'def addTab(self, widget, label):' in line and i < len(lines) - 1 and 'import sys' in lines[i+1]:
        line_to_fix = i
        break

if line_to_fix is not None:
    # Add the proper return statement and a blank line
    lines.insert(line_to_fix + 1, '        return super().addTab(widget, label)\n\n')
    # Remove the import sys line
    lines.pop(line_to_fix + 2)

    # Write the corrected file
    with open('src/main_fixed.py', 'w') as file:
        file.writelines(lines)
    print("Fixed file created as src/main_fixed.py")
else:
    print("Could not find the line to fix") 