import os
import re

def check_indentation(directories):
    issues = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f, 1):
                                if line.strip() and not line.startswith('#'):
                                    leading_spaces = len(line) - len(line.lstrip(' '))
                                    if leading_spaces % 4 != 0:
                                        issues.append(f"{file_path}:{i}: Indentation issue ({leading_spaces} spaces)")
                    except Exception as e:
                        pass
    return issues

if __name__ == "__main__":
    target_dirs = ['backend/app/services/analysis/', 'backend/tests/']
    indent_issues = check_indentation(target_dirs)
    if indent_issues:
        for issue in indent_issues:
            print(issue)
    else:
        print("No indentation issues found.")
