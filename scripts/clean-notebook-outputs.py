#!/usr/bin/env python3
"""
clean-notebook-outputs.py — Strip Jupyter Notebook output cells and execution metadata.
This prevents large binaries from bloating Git diffs and repositories.
"""

import sys
import json
import os

def clean_notebook(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)
        
    if not file_path.endswith('.ipynb'):
        print(f"Error: not a notebook file: {file_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Cleaning notebook: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON from {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Clean cells
    cells = data.get('cells', [])
    cleaned_count = 0
    
    for cell in cells:
        if cell.get('cell_type') == 'code':
            # Clear outputs
            if cell.get('outputs'):
                cell['outputs'] = []
                cleaned_count += 1
            # Clear execution count
            if cell.get('execution_count') is not None:
                cell['execution_count'] = None
                cleaned_count += 1
            # Clear metadata that can be generated during execution
            cell['metadata'] = {}

    # Clear overall notebook metadata that might contain local system info (excluding language)
    if 'metadata' in data:
        # Keep only essential metadata
        essential = {}
        for key in ['kernelspec', 'language_info']:
            if key in data['metadata']:
                essential[key] = data['metadata'][key]
        data['metadata'] = essential

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write('\n') # trailing newline
        print(f"Notebook cleaned successfully. Stripped outputs/execution counters in {cleaned_count} places.")
    except Exception as e:
        print(f"Error writing notebook to {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean-notebook-outputs.py <notebook_path>", file=sys.stderr)
        sys.exit(1)
    clean_notebook(sys.argv[1])
