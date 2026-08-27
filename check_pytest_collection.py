import os
import subprocess
import sys

def check_pytest_collection(directories):
    errors = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    # Use python -m pytest --collect-only on each file
                    try:
                        result = subprocess.run(
                            [sys.executable, "-m", "pytest", "--collect-only", file_path],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode != 0:
                            errors.append(f"Failed to collect {file_path}:\n{result.stderr}")
                    except subprocess.TimeoutExpired:
                        errors.append(f"Timeout collecting {file_path}")
                    except Exception as e:
                        errors.append(f"Error collecting {file_path}: {str(e)}")
    return errors

if __name__ == "__main__":
    target_dirs = ['backend/app/services/analysis/', 'backend/tests/']
    collection_errors = check_pytest_collection(target_dirs)
    if collection_errors:
        for err in collection_errors:
            print(err)
            print("-" * 40)
        sys.exit(1)
    else:
        print("All files collected successfully by pytest.")
        sys.exit(0)
