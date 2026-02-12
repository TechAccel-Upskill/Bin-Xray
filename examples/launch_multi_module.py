#!/usr/bin/env python3
"""
Launch Bin-Xray GUI with multi-module test example
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bin_xray import BinXrayGUI
import tkinter as tk

def main():
    root = tk.Tk()
    app = BinXrayGUI(root)
    
    # Pre-load multi-module example
    binary_path = os.path.join(os.path.dirname(__file__), 
                               'test_binaries/multi/multi_module.elf')
    map_path = os.path.join(os.path.dirname(__file__), 
                           'test_binaries/multi/multi_module.map')
    lib_dir = os.path.join(os.path.dirname(__file__), 
                          'test_binaries/multi')
    
    if os.path.exists(binary_path):
        app.binary_var.set(binary_path)
        print(f"✓ Loaded binary: {binary_path}")
    
    if os.path.exists(map_path):
        app.map_var.set(map_path)
        print(f"✓ Loaded map file: {map_path}")
    
    if os.path.exists(lib_dir):
        app.libdir_var.set(lib_dir)
        print(f"✓ Loaded library directory: {lib_dir}")
    
    print("\n" + "="*70)
    print("  BIN-XRAY - Symbol-Level Dependency Visualization")
    print("="*70)
    print("\n📌 Multi-Module Example Loaded!")
    print("\n   This example shows:")
    print("   • main.o calling functions in utils.o and math_ops.o")
    print("   • math_ops.o calling vector_magnitude() from utils.o")
    print("\n   To visualize:")
    print("   1. Check ✓ 'Show Symbol Dependencies'")
    print("   2. Click 'Analyze & Generate Graph'")
    print("   3. See function calls as labeled edges!\n")
    
    root.mainloop()

if __name__ == '__main__':
    main()
