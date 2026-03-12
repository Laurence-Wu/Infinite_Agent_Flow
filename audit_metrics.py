
import os
import re
from pathlib import Path

def get_metrics(file_path, root_dir):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()
    except Exception as e:
        return None
        
    line_count = len(lines)
    
    # func_count and max_func_len
    func_pattern = re.compile(r'^\s*(def |async def |function |const \w+ = \(.*\) =>|let \w+ = \(.*\) =>)')
    funcs = []
    current_func_start = -1
    
    for i, line in enumerate(lines):
        if func_pattern.search(line):
            if current_func_start != -1:
                funcs.append(i - current_func_start)
            current_func_start = i
    if current_func_start != -1:
        funcs.append(len(lines) - current_func_start)
        
    func_count = len(funcs)
    max_func_len = max(funcs) if funcs else 0
    
    todo_count = len([l for l in lines if any(x in l for x in ['TODO', 'FIXME', 'HACK', 'XXX'])])
    
    # magic_count (approximate)
    magic_pattern = re.compile(r'("[\w-]+_\d+"|\d{4,5}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[2-9]|\d{2,})')
    magic_count = len([l for l in lines if magic_pattern.search(l)])
    
    any_count = 0
    if file_path.suffix in ['.ts', '.tsx']:
        any_count = len([l for l in lines if ': any' in l or 'as any' in l])
        
    # has_test
    has_test = False
    name = file_path.stem
    if file_path.suffix == '.py':
        # Check in tests folder
        test_path = root_dir / 'tests' / f'test_{name}.py'
        if test_path.exists():
            has_test = True
    elif file_path.suffix in ['.ts', '.tsx']:
        test_path = file_path.with_name(f'{name}.test.ts')
        if test_path.exists():
            has_test = True
            
    try:
        rel_path = str(file_path.relative_to(root_dir))
    except ValueError:
        rel_path = str(file_path)
            
    return {
        'file': rel_path,
        'lines': line_count,
        'funcs': func_count,
        'max_func_len': max_func_len,
        'todos': todo_count,
        'magic': magic_count,
        'any_count': any_count,
        'has_test': has_test
    }

def main():
    root_dir = Path.cwd().resolve()
    skip_dirs = ['node_modules', '.next', '__pycache__', '.git', 'dist', '.venv', 'output']
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in filenames:
            if f.endswith(('.py', '.ts', '.tsx')):
                files.append(Path(root) / f)
                
    metrics = [get_metrics(f, root_dir) for f in files]
    metrics = [m for m in metrics if m is not None]
    metrics.sort(key=lambda x: x['max_func_len'], reverse=True)
    
    print('| file | lines | funcs | max_func_len | todos | magic | has_test |')
    print('|------|-------|-------|--------------|-------|-------|----------|')
    for m in metrics[:10]:
        print(f"| {m['file']} | {m['lines']} | {m['funcs']} | {m['max_func_len']} | {m['todos']} | {m['magic']} | {m['has_test']} |")

if __name__ == '__main__':
    main()
