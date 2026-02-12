# Bin-Xray Project Structure

```
Bin-xray/
├── run.py                  # Main launcher script (wrapper)
├── requirements.txt         # Python dependencies
├── setup.sh                # Installation script
├── LICENSE                 # License file
│
├── src/                    # Source code
│   └── bin_xray.py        # Core application code
│
├── docs/                   # Documentation
│   ├── README.md          # Main documentation
│   ├── QUICKSTART.md      # Quick start guide
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── PROJECT_SUMMARY.md
│   ├── TOOLS_REFERENCE.md
│   ├── SDK_EXTENSIONS.md
│   ├── SYMBOL_VISUALIZATION.md
│   └── ... (other docs)
│
├── scripts/                # Utility scripts
│   └── test_installation.py  # Test installation
│
├── examples/               # Example usage scripts
│   ├── launch_adas_test.py
│   ├── launch_multi_module.py
│   ├── compare_test_data.py
│   └── examples.py
│
├── test_binaries/          # Test data
│   ├── adas_camera/       # ADAS test case
│   ├── vim_libs/          # Vim test libraries
│   └── python3_libs/      # Python test libraries
│
└── config/                 # Configuration files (empty for now)
```

## Directory Descriptions

### `/src` - Source Code
Main application source code. Keep all Python modules here.

### `/docs` - Documentation
All markdown documentation, guides, and references.

### `/scripts` - Utility Scripts
Helper scripts for installation, testing, and maintenance.

### `/examples` - Example Usage
Demo scripts showing how to use the tool with different binaries.

### `/test_binaries` - Test Data
Sample binaries, libraries, and map files for testing and validation.

### `/config` - Configuration
Configuration files for different use cases (ready for future expansion).

## Usage

Run from project root:
```bash
python3 run.py --binary test_binaries/adas_camera/adas_camera.elf
```

Or simply launch the GUI:
```bash
python3 run.py
```
