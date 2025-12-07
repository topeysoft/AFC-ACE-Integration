#!/usr/bin/env python3
"""
AFC-ACE Config Checker
Helps diagnose "AFC_hub not found" errors by scanning your config files
"""

import sys
import os
import re

def check_config_file(filepath):
    """
    Check a single config file for hub references
    Returns list of issues found
    """
    issues = []

    if not os.path.exists(filepath):
        return [f"File not found: {filepath}"]

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        current_section = None
        for line_num, line in enumerate(lines, 1):
            # Track current section
            section_match = re.match(r'\[([^\]]+)\]', line)
            if section_match:
                current_section = section_match.group(1)

            # Check for hub references (not commented out)
            if re.match(r'^\s*hub\s*:', line):
                hub_value = line.split(':', 1)[1].strip()
                issues.append({
                    'file': filepath,
                    'line': line_num,
                    'section': current_section,
                    'content': line.strip(),
                    'hub_name': hub_value
                })

    except Exception as e:
        return [f"Error reading {filepath}: {e}"]

    return issues

def check_hub_definition(config_dir, hub_name):
    """
    Check if a hub is actually defined
    """
    # Look for [AFC_hub <hub_name>] in all .cfg files
    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith('.cfg'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if re.search(rf'\[AFC_hub\s+{hub_name}\]', content):
                            return True, filepath
                except:
                    pass

    return False, None

def main():
    print("=" * 70)
    print("AFC-ACE Config Checker")
    print("=" * 70)
    print()

    # Default config directory
    config_dir = os.path.expanduser("~/printer_data/config")

    if len(sys.argv) > 1:
        config_dir = sys.argv[1]

    if not os.path.exists(config_dir):
        print(f"❌ Config directory not found: {config_dir}")
        print()
        print("Usage:")
        print(f"  python3 {sys.argv[0]} [config_directory]")
        print()
        print("Example:")
        print(f"  python3 {sys.argv[0]} ~/printer_data/config")
        sys.exit(1)

    print(f"📁 Scanning config directory: {config_dir}")
    print()

    # Find all .cfg files
    cfg_files = []
    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith('.cfg'):
                cfg_files.append(os.path.join(root, file))

    print(f"📄 Found {len(cfg_files)} config files")
    print()

    # Check each file for hub references
    all_issues = []
    hub_names = set()

    for cfg_file in cfg_files:
        issues = check_config_file(cfg_file)
        if issues and isinstance(issues[0], dict):
            all_issues.extend(issues)
            for issue in issues:
                hub_names.add(issue['hub_name'])

    # Report findings
    if not all_issues:
        print("✅ No hub references found in config files")
        print("   (This is correct for ACE-only setups)")
        print()
        print("If you're still getting 'AFC_hub not found' error:")
        print("  1. Make sure you restarted Klipper after config changes")
        print("  2. Check that no hub: lines exist in your config")
        print("  3. Try the minimal config: config/AFC_ACE_minimal.cfg")
        sys.exit(0)

    print(f"⚠️  Found {len(all_issues)} hub reference(s):")
    print()

    for issue in all_issues:
        print(f"  File: {issue['file']}")
        print(f"  Line {issue['line']}: {issue['content']}")
        print(f"  Section: [{issue['section']}]")
        print(f"  Hub name: '{issue['hub_name']}'")

        # Check if hub is defined
        hub_defined, hub_file = check_hub_definition(config_dir, issue['hub_name'])

        if hub_defined:
            print(f"  ✅ Hub IS defined in: {hub_file}")
        else:
            print(f"  ❌ Hub NOT defined (this causes the error!)")

        print()

    # Provide solutions
    print("=" * 70)
    print("💡 SOLUTIONS:")
    print("=" * 70)
    print()

    for issue in all_issues:
        hub_defined, _ = check_hub_definition(config_dir, issue['hub_name'])

        if not hub_defined:
            print(f"To fix {issue['file']}:")
            print()
            print(f"  Option 1: Comment out the hub line (recommended for ACE-only)")
            print(f"    Change line {issue['line']} from:")
            print(f"      {issue['content']}")
            print(f"    To:")
            print(f"      # {issue['content']}")
            print()
            print(f"  Option 2: Define the hub (only if you have physical hub hardware)")
            print(f"    Add this section to your config:")
            print(f"      [AFC_hub {issue['hub_name']}]")
            print(f"      # Your hub configuration here")
            print()
            print("-" * 70)
            print()

    print("After making changes:")
    print("  1. Save your config files")
    print("  2. Run: sudo systemctl restart klipper")
    print("  3. Check Klipper log for errors")
    print()

if __name__ == '__main__':
    main()
