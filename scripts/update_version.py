#!/usr/bin/env python3
"""
Update version strings across the project.
Usage: python scripts/update_version.py 0.1.2
"""

import sys
import re
from pathlib import Path

def update_version(version):
    """Update version in key files"""
    
    files_to_update = [
        ('setup.py', r'version=["\'].*?["\']', f'version="{version}"'),
        ('converterGUI.py', r'__version__ = ["\'].*?["\']', f'__version__ = "{version}"'),
        ('reportGUI.py', r'__version__ = ["\'].*?["\']', f'__version__ = "{version}"'),
        ('.github/workflows/build-and-release.yml', r'Version: .*', f'Version: {version}'),
    ]
    
    for filepath, pattern, replacement in files_to_update:
        path = Path(filepath)
        if path.exists():
            content = path.read_text()
            updated = re.sub(pattern, replacement, content)
            path.write_text(updated)
            print(f"✓ Updated {filepath}")
        else:
            print(f"⚠ File not found: {filepath}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/update_version.py <version>")
        sys.exit(1)
    
    version = sys.argv[1]
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        print(f"Invalid version format: {version}. Use semantic versioning (e.g., 0.1.2)")
        sys.exit(1)
    
    update_version(version)
    print(f"\n✓ Version updated to {version}")
