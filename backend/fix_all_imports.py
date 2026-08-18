import os
import re

def find_and_fix_imports(project_root):
    """Find and fix common broken import patterns"""
    
    # Mapping of broken imports to correct imports
    fixes = [
        # Database session
        (r'from app\.db\.session import', r'from app.db.base import'),
        
        # Model imports - consolidate fragmented model files
        (r'from app\.models\.symbol import', r'from app.models.models import'),
        (r'from app\.models\.user import', r'from app.models.models import'),
        (r'from app\.models\.portfolio import', r'from app.models.models import'),
        (r'from app\.models\.market import', r'from app.models.models import'),
        (r'from app\.models\.news import', r'from app.models.models import'),
        (r'from app\.models\.ml import', r'from app.models.models import'),
        (r'from app\.models\.orderbook import', r'from app.models.models import'),
        (r'from app\.models\.financial import', r'from app.models.models import'),
        (r'from app\.models\.macro import', r'from app.models.models import'),
        (r'from app\.models\.screening import', r'from app.models.models import'),
        (r'from app\.models\.anomaly import', r'from app.models.models import'),
        (r'from app\.models\.notification import', r'from app.models.models import'),
        (r'from app\.models\.audit import', r'from app.models.models import'),
        
        # Services imports - core services
        (r'from app\.services\.core\.symbol_service import', r'from app.services.data.symbol_service import'),
    ]
    
    fixed_files = []
    error_files = []
    
    for root, dirs, files in os.walk(project_root):
        # Skip virtual environment and cache directories
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', 'node_modules', '.pytest_cache']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    file_fixed = False
                    
                    # Apply all fixes
                    for pattern, replacement in fixes:
                        if re.search(pattern, content):
                            content = re.sub(pattern, replacement, content)
                            file_fixed = True
                    
                    if file_fixed:
                        # Create backup
                        backup_path = f"{filepath}.backup"
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(original_content)
                        
                        # Write fixed content
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        fixed_files.append(filepath)
                    
                except Exception as e:
                    error_files.append((filepath, str(e)))
    
    return fixed_files, error_files

if __name__ == "__main__":
    project_root = r"E:\Shakour\BedaanProjects\OldFils\BedaanWaves\backend"
    print("Starting import fixes...")
    
    fixed, errors = find_and_fix_imports(project_root)
    
    print(f"\nFixed {len(fixed)} files:")
    for f in fixed[:20]:  # Show first 20
        print(f"  - {f}")
    
    if len(fixed) > 20:
        print(f"  ... and {len(fixed) - 20} more")
    
    if errors:
        print(f"\nEncountered errors in {len(errors)} files:")
        for filepath, error in errors[:10]:
            print(f"  - {filepath}: {error}")
    
    print("\nDone!")
