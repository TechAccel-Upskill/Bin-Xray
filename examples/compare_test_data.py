#!/usr/bin/env python3
"""
Compare Old vs New Test Data

This script demonstrates the improvement in test data quality by comparing:
- Old: Simple 3-file multi-module example
- New: Realistic 10-file ADAS camera system
"""

import subprocess
import sys
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    bin_xray = script_dir / "run.py"
    
    # Test data locations
    old_test = {
        'name': 'Old Test Data (Simple Multi-Module)',
        'binary': script_dir / 'test_binaries' / 'multi_module' / 'app.elf',
        'map': script_dir / 'test_binaries' / 'multi_module' / 'app.map',
        'libdir': script_dir / 'test_binaries' / 'multi_module',
        'files': 3,
        'layers': 0,
        'libraries': 0,
        'complexity': 'Toy Example'
    }
    
    new_test = {
        'name': 'New Test Data (ADAS Camera System)',
        'binary': script_dir / 'test_binaries' / 'adas_camera' / 'adas_camera.elf',
        'map': script_dir / 'test_binaries' / 'adas_camera' / 'adas_camera.map',
        'libdir': script_dir / 'test_binaries' / 'adas_camera',
        'files': 10,
        'layers': 4,
        'libraries': 3,
        'complexity': 'Production ADAS'
    }
    
    print("=" * 70)
    print("BIN-XRAY TEST DATA COMPARISON")
    print("=" * 70)
    
    print("\n📊 COMPARISON TABLE\n")
    print(f"{'Metric':<20} {'Old Test':<25} {'New Test':<25}")
    print("-" * 70)
    print(f"{'Source Files':<20} {old_test['files']:<25} {new_test['files']:<25}")
    print(f"{'Architecture Layers':<20} {old_test['layers']:<25} {new_test['layers']:<25}")
    print(f"{'Static Libraries':<20} {old_test['libraries']:<25} {new_test['libraries']:<25}")
    print(f"{'Complexity':<20} {old_test['complexity']:<25} {new_test['complexity']:<25}")
    print(f"{'Binary Exists':<20} {str(old_test['binary'].exists()):<25} {str(new_test['binary'].exists()):<25}")
    
    print("\n" + "=" * 70)
    print("CHOOSE WHICH TEST DATA TO VISUALIZE")
    print("=" * 70)
    print("\n1. Old Test Data (Simple Multi-Module)")
    print("   - 3 source files")
    print("   - Basic vector/math functions")
    print("   - ~5 symbol dependencies")
    print("   - Good for: Quick testing")
    
    print("\n2. New Test Data (ADAS Camera System) ⭐ RECOMMENDED")
    print("   - 10 source files in 4 layers")
    print("   - Realistic automotive ADAS functions")
    print("   - 50+ symbol dependencies")
    print("   - 3 static libraries (libhal.a, libdrivers.a, libalgorithms.a)")
    print("   - Good for: Validating tool efficiency")
    
    print("\n3. Both (Sequential)")
    print("   - Launch old test first, then new test")
    print("   - Compare side-by-side")
    
    print("\n" + "=" * 70)
    choice = input("\nEnter choice [1/2/3] (default=2): ").strip() or '2'
    
    if choice == '1':
        launch_test(bin_xray, old_test, "Old")
    elif choice == '2':
        launch_test(bin_xray, new_test, "New")
    elif choice == '3':
        print("\n--- Launching OLD test data first ---")
        launch_test(bin_xray, old_test, "Old")
        print("\n--- Now launching NEW test data ---")
        launch_test(bin_xray, new_test, "New")
    else:
        print("Invalid choice. Launching new test data (default).")
        launch_test(bin_xray, new_test, "New")

def launch_test(bin_xray, test_data, label):
    """Launch Bin-Xray with specific test data."""
    print(f"\n🚀 Launching: {test_data['name']}")
    print(f"   Binary: {test_data['binary'].name}")
    print(f"   Map: {test_data['map'].name if test_data['map'].exists() else 'N/A'}")
    print(f"   Library Dir: {test_data['libdir']}")
    
    # Check if files exist
    if not test_data['binary'].exists():
        print(f"\n❌ ERROR: Binary not found: {test_data['binary']}")
        if 'multi_module' in str(test_data['binary']):
            print("\nThe old test data needs to be rebuilt. Please run:")
            print("   cd test_binaries/multi_module && gcc ...")
        return
    
    cmd = [
        sys.executable,
        str(bin_xray),
        '--binary', str(test_data['binary']),
        '--libdir', str(test_data['libdir']),
        '--show-symbols',
        '--layout', 'hierarchical',
        '--depth', '6',
        '--auto'
    ]
    
    # Add map file if exists
    if test_data['map'].exists():
        cmd.extend(['--map', str(test_data['map'])])
    
    print(f"\n⏳ Analyzing {label} test data...\n")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print(f"\n{label} test visualization closed.")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()
