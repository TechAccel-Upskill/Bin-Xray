# Distribution Guide - Bin-Xray

This guide explains how to distribute Bin-Xray to users.

## Package Structure

When distributing Bin-Xray, include these files/folders:

```
Bin-xray/
├── run.py               # Main launcher (auto-setup)
├── src/                 # Core application code
├── requirements.txt     # Python dependencies
├── test_binaries/       # Test data (optional)
├── docs/                # Documentation
├── SETUP.md            # Setup instructions
├── README.md           # Overview
└── .vscode/            # VS Code configuration
    ├── launch.json     # Debug configurations
    └── settings.json   # Python interpreter settings
```

## For End Users

### Method 1: Command Line (Simplest)

Users just need to run:
```bash
python3 run.py
```

The script will automatically:
1. Create virtual environment (`.venv/`)
2. Install dependencies (`networkx`)
3. Launch the GUI

### Method 2: VS Code (For Development)

1. Open folder in VS Code
2. Press **F5** (or Run → Start Debugging)
3. Choose a configuration:
   - **Bin-Xray: ADAS Camera (Auto)** - Demo with test data
   - **Bin-Xray: GUI Mode** - Empty GUI for custom binaries
   - **Bin-Xray: Custom Binary** - Prompts for binary paths

The `.vscode/settings.json` automatically configures the Python interpreter.

## First-Time Setup for Users

### Prerequisites
Users need to install system tools:

**Ubuntu/Debian:**
```bash
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

### Running the App

**Option A: Automated (Recommended)**
```bash
python3 run.py
```
Everything else is automatic!

**Option B: Manual Setup**
```bash
# Run the setup script
./setup.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

## VS Code Launch Configurations

The included `.vscode/launch.json` provides 4 ready-to-use configurations:

1. **Bin-Xray: GUI Mode**
   - Opens empty GUI
   - User selects files manually

2. **Bin-Xray: ADAS Camera (Auto)**
   - Auto-analyzes ADAS test data
   - Perfect for demos/testing

3. **Bin-Xray: VIM Binary (Auto)**
   - Auto-analyzes VIM binary
   - Shows real-world example

4. **Bin-Xray: Custom Binary**
   - Prompts for file paths
   - Good for one-off analysis

All configurations use the virtual environment Python automatically.

## Distribution Checklist

When sharing Bin-Xray:

- ✅ Include `run.py` (main launcher)
- ✅ Include `src/` directory (core code)
- ✅ Include `requirements.txt` (dependencies)
- ✅ Include `README.md` and `SETUP.md` (documentation)
- ✅ Include `.vscode/` for VS Code users
- ✅ Optional: Include `test_binaries/` for demo data
- ⚠️ **Exclude** `.venv/` (auto-created on first run)
- ⚠️ **Exclude** `__pycache__/` (Python cache)
- ⚠️ **Exclude** `.git/` if distributing as zip

## Creating Distribution Package

### Zip Archive
```bash
cd /path/to/parent
zip -r Bin-xray-v1.0.zip Bin-xray/ \
  -x "Bin-xray/.venv/*" \
  -x "Bin-xray/.git/*" \
  -x "Bin-xray/__pycache__/*" \
  -x "Bin-xray/src/__pycache__/*"
```

### Git Repository
```bash
git clone <repository-url> Bin-xray
cd Bin-xray
python3 run.py  # Auto-setup and run
```

## User Quick Start

Users should be told:

**To run Bin-Xray:**
1. Extract the zip file
2. Open terminal in the `Bin-xray` folder
3. Run: `python3 run.py`
4. The app will auto-setup and launch

**To use in VS Code:**
1. Open `Bin-xray` folder in VS Code
2. Press **F5**
3. Select a launch configuration
4. The app will auto-setup and launch

## Troubleshooting for Users

**"No module named 'networkx'"**
→ Delete `.venv/` folder and run `python3 run.py` again

**"readelf not found"**
→ Install binutils: `sudo apt-get install binutils`

**"No module named 'tkinter'"**
→ Install tkinter: `sudo apt-get install python3-tk`

**VS Code debugger issues**
→ Make sure `.venv/bin/python3` is selected as interpreter
→ Press `Ctrl+Shift+P` → "Python: Select Interpreter" → Choose `.venv/bin/python3`
