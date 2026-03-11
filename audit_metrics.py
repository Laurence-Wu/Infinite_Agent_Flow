#!/usr/bin/env python3
"""
Audit metrics collector for CardDealer codebase.
Walks all .py and .ts/.tsx files and collects metrics.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Directories to skip
SKIP_DIRS = {
    'node_modules', '.next', '__pycache__', '.git', 'dist', 
    '.pytest_cache', '.qwen', '.claude', '.venv', 'venv'
}

# File patterns to skip
SKIP_FILES = {'*.pyc', '*.pyo'}

def should_skip_path(path: Path) -> bool:
    """Check if path should be skipped."""
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
        if part.startswith('.'):
            return True
    return False

def count_functions_py(content: str) -> tuple[int, int]:
    """Count functions and find max function length in Python file."""
    func_count = 0
    max_func_len = 0
    
    # Find all function definitions
    func_pattern = re.compile(r'^(\s*)def\s+(\w+)\s*\(', re.MULTILINE)
    lines = content.split('\n')
    
    func_starts = []
    for i, line in enumerate(lines):
        match = func_pattern.match(line)
        if match:
            indent = len(match.group(1))
            func_count += 1
            func_starts.append((i, indent))
    
    # Calculate function lengths
    for idx, (start_line, indent) in enumerate(func_starts):
        # Find end of function (next line with same or less indent that's not empty/comment)
        end_line = len(lines)
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip() and not line.strip().startswith('#'):
                # Check indent
                line_indent = len(line) - len(line.lstrip())
                if line_indent <= indent and not line.strip().startswith(')'):
                    end_line = i
                    break
        
        func_len = end_line - start_line
        if func_len > max_func_len:
            max_func_len = func_len
    
    return func_count, max_func_len

def count_functions_ts(content: str) -> tuple[int, int]:
    """Count functions and find max function length in TypeScript file."""
    func_count = 0
    max_func_len = 0
    
    # Match various function patterns
    patterns = [
        r'function\s+\w+\s*\(',           # function name()
        r'const\s+\w+\s*=\s*\([^)]*\)\s*=>',  # const name = () =>
        r'const\s+\w+\s*=\s*async\s*\([^)]*\)\s*=>',  # const name = async () =>
        r'\w+\s*\([^)]*\)\s*{',           # method() {
        r'\w+\s*:\s*\([^)]*\)\s*=>',      # method: () =>
    ]
    
    lines = content.split('\n')
    func_starts = []
    
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line):
                func_count += 1
                func_starts.append(i)
                break
    
    # Simple estimation: assume average function length
    if func_count > 0 and len(lines) > 0:
        avg_len = len(lines) // max(func_count, 1)
        max_func_len = min(avg_len * 2, len(lines))  # Estimate
    
    return func_count, max_func_len

def count_todos(content: str) -> int:
    """Count TODO, FIXME, HACK, XXX comments."""
    patterns = [r'TODO', r'FIXME', r'HACK', r'XXX']
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return count

def count_magic_values(content: str, is_ts: bool = False) -> int:
    """Count hardcoded magic values."""
    count = 0
    
    # Port numbers (common patterns)
    port_pattern = r'[:=\s](\d{3,5})\s*[,;\)\]}]'
    for match in re.finditer(port_pattern, content):
        val = int(match.group(1))
        if val not in (0, 1) and (val < 100 or val in [5000, 3000, 8080, 8000, 4040, 4041]):
            count += 1
    
    # IP addresses
    ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    count += len(re.findall(ip_pattern, content))
    
    # String literals that look like hardcoded IDs
    id_pattern = r'["\']agent_\d+["\']'
    count += len(re.findall(id_pattern, content))
    
    # Other hardcoded string constants (excluding common words)
    string_pattern = r'["\']([a-zA-Z_][a-zA-Z0-9_]{5,})["\']'
    common_words = {'function', 'undefined', 'null', 'string', 'number', 'boolean'}
    for match in re.finditer(string_pattern, content):
        val = match.group(1)
        if val.lower() not in common_words:
            # Check if it's in a type context
            line = content[max(0, match.start()-50):match.end()+50]
            if 'type' not in line.lower()[:20]:
                count += 1
    
    return count

def count_any_types(content: str) -> int:
    """Count : any or as any occurrences (TypeScript only)."""
    count = 0
    count += len(re.findall(r':\s*any\b', content))
    count += len(re.findall(r'\bany\s*as\b', content))
    count += len(re.findall(r'<any>', content))
    return count

def has_test_file(source_path: Path, test_files: set) -> bool:
    """Check if a matching test file exists."""
    name = source_path.stem
    
    # For Python: test_<name>.py or <name>_test.py
    if source_path.suffix == '.py':
        return (f'test_{name}.py' in test_files or 
                f'{name}_test.py' in test_files)
    
    # For TypeScript: <name>.test.ts or <name>.spec.ts
    if source_path.suffix in ('.ts', '.tsx'):
        return (f'{name}.test.ts' in test_files or
                f'{name}.spec.ts' in test_files or
                f'{name}.test.tsx' in test_files)
    
    return False

def analyze_file(path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a single file and return metrics."""
    try:
        content = path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        return None
    
    lines = content.split('\n')
    line_count = len(lines)
    
    is_ts = path.suffix in ('.ts', '.tsx')
    
    if is_ts:
        func_count, max_func_len = count_functions_ts(content)
        any_count = count_any_types(content)
    else:
        func_count, max_func_len = count_functions_py(content)
        any_count = 0
    
    todo_count = count_todos(content)
    magic_count = count_magic_values(content, is_ts)
    
    return {
        'path': str(path),
        'line_count': line_count,
        'func_count': func_count,
        'max_func_len': max_func_len,
        'todo_count': todo_count,
        'magic_count': magic_count,
        'any_count': any_count,
    }

def collect_test_files(root: Path) -> set:
    """Collect all test file names."""
    test_files = set()
    for path in root.rglob('*'):
        if path.is_file() and path.parent.name == 'tests':
            test_files.add(path.name)
    return test_files

def main():
    root = Path(__file__).parent
    
    # Collect test files
    test_files = collect_test_files(root)
    
    # Find all source files
    results = []
    
    for ext in ['*.py', '*.ts', '*.tsx']:
        for path in root.rglob(ext):
            if should_skip_path(path):
                continue
            
            metrics = analyze_file(path)
            if metrics:
                metrics['has_test'] = has_test_file(path, test_files)
                results.append(metrics)
    
    # Sort by max_func_len descending
    results.sort(key=lambda x: x['max_func_len'], reverse=True)
    
    # Print summary
    print(f"Analyzed {len(results)} files")
    print("\nTop 10 files by max_func_len:")
    print("-" * 100)
    print(f"{'File':<60} {'Lines':>8} {'Funcs':>6} {'MaxLen':>8} {'TODOs':>6} {'Magic':>6} {'Test':>6}")
    print("-" * 100)
    
    for r in results[:10]:
        rel_path = os.path.relpath(r['path'], root)
        print(f"{rel_path:<60} {r['line_count']:>8} {r['func_count']:>6} {r['max_func_len']:>8} {r['todo_count']:>6} {r['magic_count']:>6} {str(r['has_test']):>6}")
    
    # Files without tests
    no_test = [r for r in results if not r['has_test']]
    print(f"\n\nFiles without matching test: {len(no_test)}")
    for r in no_test:
        rel_path = os.path.relpath(r['path'], root)
        print(f"  - {rel_path}")
    
    return results

if __name__ == '__main__':
    main()
