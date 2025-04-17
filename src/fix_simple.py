# Open and read the file
with open('src/main.py', 'r', encoding='utf-8') as file:
    content = file.read()

# Replace the problematic line
fixed_content = content.replace('def addTab(self, widget, label):\nimport sys', 
                              'def addTab(self, widget, label):\n        return super().addTab(widget, label)\n\nimport sys')

# Write the fixed content to a new file
with open('src/main_fixed.py', 'w', encoding='utf-8') as file:
    file.write(fixed_content)

print("Fixed file created at src/main_fixed.py") 