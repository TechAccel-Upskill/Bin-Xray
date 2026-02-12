#!/usr/bin/env python3
"""
Launch Bin-Xray with ADAS Camera Test Data

This script demonstrates the tool's efficiency with realistic automotive/ADAS test data.

The ADAS camera pipeline includes:
- 10 source files organized in 4 architectural layers
- 3 static libraries (libhal.a, libdrivers.a, libalgorithms.a)
- 50+ function symbols with cross-layer dependencies
- Realistic embedded systems structure (HAL → Drivers → Algorithms → Application)
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    # Paths
    script_dir = Path(__file__).parent
    adas_dir = script_dir / "test_binaries" / "adas_camera"
    bin_xray = script_dir / "run.py"
    
    # Files
    binary_file = adas_dir / "adas_camera.elf"
    map_file = adas_dir / "adas_camera.map"
    lib_dir = adas_dir
    
    # Check if files exist
    if not binary_file.exists():
        print(f"ERROR: Binary not found: {binary_file}")
        print("\nPlease build the ADAS camera project first:")
        print(f"  cd {adas_dir}")
        print(f"  ./build.sh")
        sys.exit(1)
    
    if not map_file.exists():
        print(f"WARNING: Map file not found: {map_file}")
        print("Symbol dependencies may not be complete.\n")
    
    # Print info
    print("=" * 70)
    print("Bin-Xray - ADAS Camera Test Data Validation")
    print("=" * 70)
    print(f"\n📂 Binary:      {binary_file}")
    print(f"📂 Map File:    {map_file}")
    print(f"📂 Library Dir: {lib_dir}")
    
    # Check what's in the library directory
    print(f"\n📚 Libraries found:")
    for lib in sorted(lib_dir.glob("*.a")):
        size_kb = lib.stat().st_size / 1024
        print(f"   - {lib.name} ({size_kb:.1f} KB)")
    
    print(f"\n🔧 Object files found:")
    for obj in sorted(lib_dir.glob("*.o")):
        size_kb = obj.stat().st_size / 1024
        print(f"   - {obj.name} ({size_kb:.1f} KB)")
    
    # Show complexity
    print("\n📊 Test Data Complexity:")
    print("   - 4 architectural layers (HAL → Drivers → Algorithms → Application)")
    print("   - 10 C source files")
    print("   - 3 static libraries (.a archives)")
    print("   - 50+ function symbols")
    print("   - Multi-layer cross-dependencies")
    
    # Show what to expect
    print("\n🎯 Expected Graph Features:")
    print("   ✓ 4-layer hierarchical structure")
    print("   ✓ Library containment nodes")
    print("   ✓ Symbol-level dependencies (with 'Show Symbol Dependencies')")
    print("   ✓ Cross-references from map file")
    
    # Instructions
    print("\n" + "=" * 70)
    print("INSTRUCTIONS:")
    print("=" * 70)
    print("1. When the GUI opens, the following fields will be filled:")
    print(f"   - Binary: {binary_file.name}")
    print(f"   - Map File: {map_file.name}")
    print(f"   - Library Dir: {lib_dir}")
    print("\n2. Configure visualization options:")
    print("   ✓ Check 'Show Symbol Dependencies' (to see function calls)")
    print("   - Set Layout: 'hierarchical' (best for layered architecture)")
    print("   - Max Depth: 6 or higher")
    print("\n3. Click 'Analyze & Generate Graph'")
    print("\n4. Observe:")
    print("   - HAL layer at bottom (hal_gpio, hal_i2c, hal_spi)")
    print("   - Driver layer above HAL (driver_camera, driver_can)")
    print("   - Algorithm layer (image_processing, lane_detection, object_detection)")
    print("   - Application layer at top (vehicle_control, main_adas)")
    print("\n5. Look for symbol edges (dashed teal lines with function names)")
    print("   - Example: main_adas.o --[Camera_Init]--> driver_camera.o")
    print("=" * 70)
    
    # Launch
    print("\n🚀 Launching Bin-Xray GUI with ADAS files pre-loaded...\n")
    
    # Build command with all arguments
    cmd = [
        sys.executable,
        str(bin_xray),
        '--binary', str(binary_file),
        '--map', str(map_file),
        '--libdir', str(lib_dir),
        '--show-symbols',
        '--layout', 'hierarchical',
        '--depth', '6',
        '--auto'  # Automatically analyze
    ]
    
    print("📝 Command:")
    print("   " + " ".join(cmd))
    print("\n⏳ Analyzing ADAS dependencies...\n")
    
    # Run run.py with arguments
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\nBin-Xray closed by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Failed to launch Bin-Xray: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
