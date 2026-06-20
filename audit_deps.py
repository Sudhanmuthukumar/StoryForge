import os
import ast
import sys
import json

root_dir = r"c:\StoryForge AI"
stdlib = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set() # Available in Python 3.10+

imports_by_file = {}
all_third_party = set()

# Internal module packages
internal_packages = {'core', 'modules', 'ui', 'services', 'utils', 'tests', 'dataset_lab', 'models', 'config', 'main'}

for root, _, files in os.walk(root_dir):
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=filepath)
                
                file_imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            file_imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            file_imports.add(node.module.split('.')[0])
                
                # filter out stdlib and internal packages
                external = {imp for imp in file_imports if imp not in stdlib and imp not in internal_packages and not imp.startswith('_')}
                
                if external:
                    rel_path = os.path.relpath(filepath, root_dir)
                    imports_by_file[rel_path] = list(external)
                    all_third_party.update(external)
            except Exception as e:
                pass

output = {
    "imports_by_file": imports_by_file,
    "all_third_party": list(all_third_party)
}
print(json.dumps(output, indent=2))
