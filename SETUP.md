# Bin-Xray Setup Guide

## Prerequisites

### System Dependencies
Install required system tools for binary analysis:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install binutils file python3-tk python3-venv
```

**Fedora/RHEL:**
```bash
sudo dnf install binutils file python3-tkinter python3-venv
```

**macOS:**
```bash
brew install binutils
```

## Installation Steps

### 1. Clone/Download the Repository
```bash
cd /path/to/your/workspace
git clone <repository-url> Bin-xray
cd Bin-xray
```

### 2. Create Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
# Run the test script
python3 scripts/test_installation.py

# Or launch the GUI
python3 run.py
```

## Running Bin-Xray

### GUI Mode
```bash
# Activate virtual environment first
source .venv/bin/activate

# Launch GUI
python3 run.py
```

### Command-Line Mode (Auto-Analysis)
```bash
source .venv/bin/activate

python3 run.py \
  --binary test_binaries/adas_camera/adas_camera.elf \
  --map test_binaries/adas_camera/adas_camera.map \
  --libdir test_binaries/adas_camera/ \
  --show-symbols \
  --auto
```

### Available Test Binaries
- **ADAS Camera**: `test_binaries/adas_camera/` - Automotive ADAS system test data
- **VIM Binary**: `test_binaries/vim.elf` - Real-world binary with 11+ shared libraries

## VS Code Setup (Optional)

### 1. Select Python Interpreter
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type "Python: Select Interpreter"
3. Choose `.venv/bin/python` from the list

### 2. Run with Debugger
Press `F5` and select one of the launch configurations:
- **Bin-Xray: GUI Mode** - Interactive GUI
- **Bin-Xray: ADAS Camera (Auto)** - Auto-analyze test data
- **Bin-Xray: VIM Binary (Auto)** - Analyze VIM binary
- **Bin-Xray: Custom Binary** - Analyze your own binary

## Troubleshooting

### "No module named 'networkx'"
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "No module named 'tkinter'"
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

### Binary Analysis Tools Not Found
```bash
# Verify tools are installed
which readelf nm objdump ar

# Install if missing (Ubuntu)
sudo apt-get install binutils
```

## Project Structure
```
Bin-xray/
├── run.py               # Main entry point (wrapper)
├── src/
│   └── bin_xray.py      # Core application code
├── docs/                # Documentation
├── examples/            # Example scripts
├── scripts/             # Utility scripts
├── test_binaries/       # Test data
├── config/              # Configuration files
├── requirements.txt     # Python dependencies
└── .vscode/
    └── launch.json      # VS Code debug configurations
```

## Deactivating Virtual Environment
```bash
deactivate
```

## Additional Resources
- **README.md** - Project overview and features
- **docs/** - Detailed documentation
- **examples/** - Example usage scripts
