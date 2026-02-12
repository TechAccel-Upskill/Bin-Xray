#!/usr/bin/env python3
"""
Bin-Xray: Binary Dependency Analyzer
Wrapper script with auto-setup capabilities
"""
import sys
import os
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_DIR = SCRIPT_DIR / '.venv'
REQUIREMENTS_FILE = SCRIPT_DIR / 'requirements.txt'
VENV_PYTHON = VENV_DIR / 'bin' / 'python3'

def is_debugger_active():
    """Detect if running under a debugger (VS Code, PyCharm, etc.)."""
    return (
        sys.gettrace() is not None or  # Debugger trace function active
        'debugpy' in sys.modules or     # VS Code debugger
        'pydevd' in sys.modules or      # PyCharm debugger
        'PYTHONBREAKPOINT' in os.environ
    )

def is_venv_active():
    """Check if already running in a virtual environment."""
    return (
        hasattr(sys, 'real_prefix') or  # Old virtualenv
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)  # venv
    )

def check_system_tools():
    """Check if required system tools are installed."""
    missing_tools = []
    for tool in ['readelf', 'nm', 'objdump', 'ar']:
        if subprocess.run(['which', tool], capture_output=True).returncode != 0:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"⚠️  Warning: Missing system tools: {', '.join(missing_tools)}")
        print("Install with:")
        print("  Ubuntu/Debian: sudo apt-get install binutils file python3-tk")
        print("  Fedora/RHEL:   sudo dnf install binutils file python3-tkinter")
        print()

def ensure_venv():
    """Ensure virtual environment exists."""
    if not VENV_DIR.exists():
        print("📦 Virtual environment not found. Creating...")
        try:
            subprocess.run([sys.executable, '-m', 'venv', str(VENV_DIR)], check=True)
            print("✓ Virtual environment created at .venv/")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            print("Please install python3-venv:")
            print("  Ubuntu/Debian: sudo apt-get install python3-venv")
            sys.exit(1)
    return False

def install_dependencies_if_needed(python_exe):
    """Install dependencies if not already installed."""
    try:
        # Check if networkx is installed
        result = subprocess.run(
            [str(python_exe), '-c', 'import networkx'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("📦 Installing dependencies...")
            if not REQUIREMENTS_FILE.exists():
                print(f"❌ {REQUIREMENTS_FILE} not found!")
                sys.exit(1)
            
            # Upgrade pip first
            subprocess.run(
                [str(python_exe), '-m', 'pip', 'install', '--upgrade', 'pip', '--quiet'],
                check=True
            )
            
            # Install requirements
            subprocess.run(
                [str(python_exe), '-m', 'pip', 'install', '-r', str(REQUIREMENTS_FILE)],
                check=True
            )
            print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Try running manually:")
        print(f"  source .venv/bin/activate")
        print(f"  pip install -r requirements.txt")
        sys.exit(1)

def run_via_subprocess(venv_python):
    """Run the main application via subprocess using venv Python."""
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = str(VENV_DIR)
    
    if 'PYTHONHOME' in env:
        del env['PYTHONHOME']
    
    src_dir = SCRIPT_DIR / 'src'
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{src_dir}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = str(src_dir)
    
    try:
        result = subprocess.run(
            [str(venv_python), str(src_dir / 'bin_xray.py')] + sys.argv[1:],
            env=env
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n👋 Bin-Xray terminated by user")
        sys.exit(0)

def run_directly():
    """Run the application directly by importing (for debugger support)."""
    # Add src to path
    src_dir = SCRIPT_DIR / 'src'
    sys.path.insert(0, str(src_dir))
    
    try:
        # Import and run main
        from bin_xray import main
        main()
    except ImportError as e:
        print(f"❌ Failed to import bin_xray: {e}")
        print("\nDependencies may not be installed in your current Python environment.")
        print("Solution:")
        print("1. In VS Code: Select the virtual environment interpreter:")
        print("   Press Ctrl+Shift+P → 'Python: Select Interpreter' → Choose '.venv/bin/python3'")
        print("\n2. Or run from terminal:")
        print("   source .venv/bin/activate")
        print("   python3 bin_xray.py")
        sys.exit(1)

def main():
    """Main entry point with auto-setup."""
    in_debugger = is_debugger_active()
    in_venv = is_venv_active()
    
    # Check system tools (warning only)
    check_system_tools()
    
    if in_debugger or in_venv:
        # Running in debugger or already in venv - run directly
        # Ensure venv exists for future runs
        if not in_venv:
            ensure_venv()
            install_dependencies_if_needed(VENV_PYTHON)
            print("\n⚠️  Note: Debugger is using system Python. For best results:")
            print("   In VS Code: Ctrl+Shift+P → 'Python: Select Interpreter' → Choose '.venv/bin/python3'")
            print("\nContinuing with current Python environment...\n")
        run_directly()
    else:
        # Normal terminal run - use venv via subprocess
        ensure_venv()
        install_dependencies_if_needed(VENV_PYTHON)
        run_via_subprocess(VENV_PYTHON)

if __name__ == '__main__':
    main()


