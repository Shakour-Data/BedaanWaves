import os
import sys

def check_files(directories):
    errors = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        compile(content, file_path, 'exec')
                    except (SyntaxError, IndentationError) as e:
                        errors.append(f"{file_path}:{e.lineno}: {e.msg}")
                    except Exception as e:
                        # Skip other errors like encoding or file access for now
                        pass
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
