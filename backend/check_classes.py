#!/usr/bin/env python
# Check available classes in ingestion service
import re
with open('E:/Shakour/BedaanProjects/OldFils/BedaanWaves/backend/app/services/data/ingestion_service.py', 'r', encoding='utf-8') as f:
    content = f.read()
    classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
    print('Classes in ingestion_service.py:')
    for c in classes:
        print(f'  - {c}')