import os
import re

def fix_imports_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace import settings with import Settings
    new_content = content.replace(
        'from app.core.config import settings',
        'from app.core.config import Settings'
    )
    
    # Also fix any usage of settings (lowercase) that should be Settings (uppercase)
    # But be careful - settings could be used as a variable name too
    # For now, just fix the import
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

backend_dir = r'E:\Shakour\BedaanProjects\OldFils\BedaanWaves\backend'
fixed_count = 0

for root, dirs, files in os.walk(backend_dir):
    # Skip .venv
    if '.venv' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            if fix_imports_in_file(filepath):
                fixed_count += 1
                print(f"Fixed: {filepath}")

print(f"\nTotal files fixed: {fixed_count}")