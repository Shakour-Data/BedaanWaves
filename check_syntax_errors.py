import os
import py_compile
import sys

def check_files(directories):
    errors = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        py_compile.compile(file_path, doraise=True)
                    except py_compile.PyCompileError as e:
                        errors.append(str(e))
                    except Exception as e:
                        errors.append(f"Error in {file_path}: {str(e)}")
    return errors

if __name__ == "__main__":
    target_dirs = ['backend/app/services/analysis/', 'backend/tests/']
    all_errors = check_files(target_dirs)
    if all_errors:
        for err in all_errors:
            print(err)
        sys.exit(1)
    else:
        print("No syntax or indentation errors found.")
        sys.exit(0)
