#!/usr/bin/env python
# Check all services
import re
import os

base_dir = 'E:/Shakour/BedaanProjects/OldFils/BedaanWaves/backend/app/services'
classes = []

for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.py') and f != '__pycache__' and f != '__init__.py':
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Find classes in this file
                file_classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                for c in file_classes:
                    classes.append((path, c))

print('Services found:')
for path, cls in classes:
    print(f'  {cls} -> {path}')
