import fileinput
import sys

# Create output file
with open('src/main_fixed.py', 'w') as out_file:
    # Read input file
    for line in fileinput.input('src/main.py'):
        # Fix the addTab method at line 937-938
        if 'def addTab(self, widget, label):' in line:
            out_file.write(line)
            # Add proper implementation for addTab method
            out_file.write('        return super().addTab(widget, label)\n\n')
            # Skip the next line which is 'import sys'
            next_line = next(fileinput.input())
            if 'import sys' in next_line:
                continue
        else:
            out_file.write(line)

print("Fixed version created in src/main_fixed.py") 