#!/usr/bin/env python3
"""
AFC-ACE Full Diagnostic Tool
Checks the entire AFC configuration for potential issues
"""

import sys
import os
import re

def scan_for_pattern(config_dir, pattern, description):
    """Scan all config files for a pattern"""
    results = []

    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith('.cfg'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            results.append({
                                'file': filepath,
                                'line': line_num,
                                'content': line.strip()
                            })
                except:
                    pass

    if results:
        print(f"\n{description}:")
        for r in results:
            rel_path = r['file'].replace(config_dir, '.')
            print(f"  {rel_path}:{r['line']}")
            print(f"    {r['content']}")

    return results

def main():
    config_dir = os.path.expanduser("~/printer_data/config")

    if len(sys.argv) > 1:
        config_dir = sys.argv[1]

    print("=" * 70)
    print("AFC-ACE Full Diagnostic")
    print("=" * 70)
    print(f"\n📁 Config directory: {config_dir}\n")

    # Check 1: AFC base configuration
    print("🔍 Checking AFC base configuration...")
    afc_cfg = os.path.join(config_dir, 'AFC', 'AFC.cfg')
    if os.path.exists(afc_cfg):
        print(f"  ✅ Found AFC.cfg")
    else:
        print(f"  ❌ AFC.cfg not found at {afc_cfg}")
        print(f"     AFC must be installed first!")

    # Check 2: ACE configuration
    print("\n🔍 Checking ACE configuration...")
    ace_configs = []
    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if 'ACE' in file and file.endswith('.cfg'):
                ace_configs.append(os.path.join(root, file))

    if ace_configs:
        print(f"  ✅ Found {len(ace_configs)} ACE config file(s):")
        for cfg in ace_configs:
            print(f"     {cfg}")
    else:
        print(f"  ⚠️  No ACE config files found")

    # Check 3: Look for ALL hub references
    print("\n🔍 Scanning for hub references...")
    hub_refs = scan_for_pattern(
        config_dir,
        r'^\s*hub\s*:',
        "Hub references found"
    )

    if not hub_refs:
        print("  ✅ No uncommented hub references")

    # Check 4: Look for AFC_hub definitions
    print("\n🔍 Checking for hub definitions...")
    hub_defs = scan_for_pattern(
        config_dir,
        r'\[AFC_hub\s+',
        "Hub definitions found"
    )

    if not hub_defs:
        print("  ℹ️  No AFC_hub sections defined (OK for ACE-only)")

    # Check 5: Look for AFC unit types
    print("\n🔍 Checking AFC units...")

    units = {}
    for unit_type in ['AFC_ACE', 'AFC_BoxTurtle', 'AFC_NightOwl', 'AFC_HTLF']:
        unit_refs = scan_for_pattern(
            config_dir,
            rf'\[{unit_type}\s+',
            f"{unit_type} units"
        )
        if unit_refs:
            units[unit_type] = len(unit_refs)

    if units:
        print("\n  Unit summary:")
        for unit_type, count in units.items():
            print(f"    {unit_type}: {count}")
    else:
        print("  ⚠️  No AFC units found!")

    # Check 6: Look for AFC lanes
    print("\n🔍 Checking AFC lanes...")
    lanes = scan_for_pattern(
        config_dir,
        r'\[AFC_lane\s+',
        "AFC lanes found"
    )

    if lanes:
        print(f"  ✅ Found {len(lanes)} lane(s)")
    else:
        print("  ⚠️  No AFC lanes found!")

    # Check 7: Look for extruder references
    print("\n🔍 Checking extruder configuration...")
    extruders = scan_for_pattern(
        config_dir,
        r'^\s*extruder\s*:',
        "Extruder references"
    )

    if extruders:
        print(f"  ✅ Found {len(extruders)} extruder reference(s)")
    else:
        print("  ⚠️  No extruder references found")

    # Check 8: Look for AFC_extruder definitions
    print("\n🔍 Checking AFC_extruder definitions...")
    afc_extruders = scan_for_pattern(
        config_dir,
        r'\[AFC_extruder\s+',
        "AFC_extruder sections"
    )

    if not afc_extruders:
        print("  ℹ️  No AFC_extruder sections (may be OK)")

    # Check 9: Look for potential issues
    print("\n🔍 Checking for potential issues...")

    # Check for lanes with explicit hub but no hub defined
    if hub_refs and not hub_defs:
        print("  ❌ ISSUE FOUND: Hub referenced but not defined!")
        print("     This is likely causing your error.")
        print("     Files with hub references:")
        for ref in hub_refs:
            rel_path = ref['file'].replace(config_dir, '.')
            print(f"       {rel_path}:{ref['line']}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if hub_refs and not hub_defs:
        print("\n❌ ERROR CAUSE IDENTIFIED:")
        print("   You have 'hub:' references in your config but no [AFC_hub] definition.")
        print("\n   SOLUTION 1 (Recommended for ACE-only):")
        print("   Comment out ALL hub: lines in these files:")
        for ref in hub_refs:
            rel_path = ref['file'].replace(config_dir, '.')
            print(f"     - {rel_path}:{ref['line']}")
        print("\n   SOLUTION 2 (Only if you have physical AFC hub):")
        print("   Add an [AFC_hub hub] section to your config")

    elif not ace_configs:
        print("\n⚠️  No ACE configuration found")
        print("   Run: python3 detect_ace_devices.py --generate-config")

    elif not lanes:
        print("\n⚠️  No AFC lanes configured")
        print("   Check your ACE configuration file")

    else:
        print("\n✅ Configuration looks good!")
        print("   If you're still getting errors:")
        print("   1. Check Klipper log: tail -50 ~/printer_data/logs/klippy.log")
        print("   2. Make sure you restarted Klipper after config changes")
        print("   3. Try the minimal config: AFC_ACE_minimal.cfg")

    print()

if __name__ == '__main__':
    main()
