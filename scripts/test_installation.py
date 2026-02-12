#!/usr/bin/env python3
"""
Test script for Bin-Xray - verifies installation and basic functionality
"""

import sys
import os
import subprocess

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def test_python_version():
    """Check Python version."""
    print_header("Python Version Check")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 7:
        print("✓ Python version is compatible (3.7+)")
        return True
    else:
        print("✗ Python 3.7+ required")
        return False

def test_imports():
    """Test required Python packages."""
    print_header("Python Package Check")
    
    packages = {
        'tkinter': 'tkinter (standard library)',
        'networkx': 'NetworkX',
        'matplotlib': 'Matplotlib'
    }
    
    results = {}
    
    for module, name in packages.items():
        try:
            if module == 'tkinter':
                import tkinter
                print(f"✓ {name}: {tkinter.TkVersion}")
            elif module == 'networkx':
                import networkx as nx
                print(f"✓ {name}: {nx.__version__}")
            elif module == 'matplotlib':
                import matplotlib
                print(f"✓ {name}: {matplotlib.__version__}")
            results[module] = True
        except ImportError as e:
            print(f"✗ {name}: NOT INSTALLED")
            print(f"  Install with: pip install {module}")
            results[module] = False
    
    return all(results.values())

def test_system_tools():
    """Test required system tools."""
    print_header("System Tools Check")
    
    tools = {
        'readelf': 'Read ELF files',
        'nm': 'Symbol extraction',
        'objdump': 'Object file analysis',
        'ar': 'Archive handling',
        'file': 'File type detection'
    }
    
    results = {}
    
    for tool, description in tools.items():
        try:
            result = subprocess.run(['which', tool], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                # Get version
                ver_result = subprocess.run([tool, '--version'],
                                          capture_output=True, text=True)
                version = ver_result.stdout.splitlines()[0] if ver_result.returncode == 0 else 'unknown'
                print(f"✓ {tool}: {path}")
                print(f"  {version[:60]}")
                results[tool] = True
            else:
                print(f"✗ {tool}: NOT FOUND ({description})")
                results[tool] = False
        except Exception as e:
            print(f"✗ {tool}: ERROR - {e}")
            results[tool] = False
    
    return all(results.values())

def test_bin_xray_import():
    """Test importing bin_xray module."""
    print_header("Bin-Xray Module Check")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        import bin_xray
        
        print("✓ bin_xray module imported successfully")
        
        # Test class imports
        from bin_xray import BinaryParser, MapFileParser, LibraryParser
        from bin_xray import DependencyGraphBuilder, BinXrayGUI
        
        print("✓ All classes imported successfully")
        
        # Test parser initialization
        parser = BinaryParser()
        print(f"✓ BinaryParser initialized")
        print(f"  Detected {len(parser.tools)} system tools")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to import bin_xray: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graph_creation():
    """Test basic graph creation."""
    print_header("Graph Creation Test")
    
    try:
        import networkx as nx
        from bin_xray import DependencyGraphBuilder
        
        # Create a test graph
        builder = DependencyGraphBuilder(max_depth=5)
        
        # Add some test data
        from bin_xray import BinaryInfo, Symbol
        
        test_binary = BinaryInfo(
            path="/test/app.elf",
            name="app.elf",
            format="ELF",
            architecture="ARM"
        )
        
        test_binary.defined_symbols = [
            Symbol(name="main", type="T", address=0x1000, size=100),
            Symbol(name="init", type="T", address=0x2000, size=50)
        ]
        
        test_binary.dynamic_deps = ["libc.so.6", "libm.so.6"]
        
        graph = builder.build_graph(binary_info=test_binary)
        
        print(f"✓ Created test graph:")
        print(f"  Nodes: {graph.number_of_nodes()}")
        print(f"  Edges: {graph.number_of_edges()}")
        
        # Test layout
        import matplotlib.pyplot as plt
        pos = nx.spring_layout(graph)
        print(f"✓ Graph layout computed: {len(pos)} positions")
        
        return True
        
    except Exception as e:
        print(f"✗ Graph creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_creation():
    """Test GUI initialization (without showing)."""
    print_header("GUI Initialization Test")
    
    try:
        import tkinter as tk
        from bin_xray import BinXrayGUI
        
        # Create root window (hidden)
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        # Try to create GUI
        app = BinXrayGUI(root)
        
        print("✓ GUI initialized successfully")
        print("✓ All widgets created")
        
        # Clean up
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_summary(results):
    """Print test summary."""
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"\nTests run: {total}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    
    if failed == 0:
        print("\n🎉 All tests passed! Bin-Xray is ready to use.")
        print("\nRun the application with:")
        print("  python3 run.py")
    else:
        print("\n⚠️  Some tests failed. Please install missing dependencies:")
        print("\nFor Python packages:")
        print("  pip install -r requirements.txt")
        print("\nFor system tools:")
        print("  sudo apt-get install binutils file  # Ubuntu/Debian")
        print("  sudo dnf install binutils file      # Fedora/RHEL")
        print("  brew install binutils               # macOS")
    
    print()
    
    return failed == 0

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  Bin-Xray Installation Test")
    print("="*70)
    
    results = {}
    
    # Run tests
    results['Python Version'] = test_python_version()
    results['Python Packages'] = test_imports()
    results['System Tools'] = test_system_tools()
    results['Module Import'] = test_bin_xray_import()
    results['Graph Creation'] = test_graph_creation()
    results['GUI Initialization'] = test_gui_creation()
    
    # Print summary
    success = print_summary(results)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
