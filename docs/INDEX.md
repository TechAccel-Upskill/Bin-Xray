# Bin-Xray - Complete Documentation Index

Welcome to Bin-Xray! This file helps you navigate all the documentation.

## 🚀 Getting Started (Start Here!)

1. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start guide
   - Installation in 3 steps
   - Your first analysis
   - Common workflows

## 📚 Main Documentation

2. **[README.md](README.md)** - Complete user guide
   - Full feature overview
   - Detailed installation instructions
   - Usage examples
   - FAQ and troubleshooting
   - Configuration guide

## 🔧 Technical References

3. **[TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)** - System tools documentation
   - Required binutils (readelf, nm, objdump, etc.)
   - Installation by platform (Ubuntu, macOS, etc.)
   - SDK-specific toolchain setup (TI, ARM, Qualcomm, etc.)
   - Tool detection and configuration

4. **[SDK_EXTENSIONS.md](SDK_EXTENSIONS.md)** - SDK customization guide
   - TI Jacinto TDA4VM specifics
   - NXP S32K support
   - Qualcomm Hexagon/SNPE
   - How to add custom map format parsers
   - Complete extension examples

5. **[ALTERNATIVES.md](ALTERNATIVES.md)** - Alternative frameworks
   - PyQt5/6 + PyGraphviz (for better performance)
   - Dear PyGui (GPU-accelerated)
   - Plotly Dash (web-based)
   - Performance comparison matrix
   - When to use alternatives

## 📦 Project Information

6. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview
   - What was built
   - Architecture overview
   - Feature checklist
   - Code quality metrics
   - Deployment options

7. **[LICENSE](LICENSE)** - MIT License
   - Free to use commercially
   - Open source friendly

## 🎯 Quick Reference by Task

### I want to...

#### ...install Bin-Xray
→ See [QUICKSTART.md - Installation](QUICKSTART.md#installation)

#### ...analyze my first binary
→ See [QUICKSTART.md - First Analysis](QUICKSTART.md#first-analysis)

#### ...configure TI Jacinto SDK tools
→ See [SDK_EXTENSIONS.md - TI Processor SDK](SDK_EXTENSIONS.md#ti-processor-sdk)

#### ...understand what tools are needed
→ See [TOOLS_REFERENCE.md - Required Tools](TOOLS_REFERENCE.md#required-tools)

#### ...handle large graphs (>1000 nodes)
→ See [ALTERNATIVES.md - PyQt + PyGraphviz](ALTERNATIVES.md#alternative-1-pyqt56--pygraphviz)

#### ...add support for my custom SDK
→ See [SDK_EXTENSIONS.md - Custom Map Formats](SDK_EXTENSIONS.md#custom-map-file-formats)

#### ...export graphs for documentation
→ See [README.md - Export Capabilities](README.md#export-capabilities)

#### ...troubleshoot errors
→ See [README.md - Troubleshooting](README.md#troubleshooting)

#### ...use Bin-Xray programmatically
→ See [examples.py](examples.py) - Contains 5 usage examples

#### ...test my installation
→ Run `./test_installation.py`

## 📁 File Overview

### Core Application
- **run.py** - Main launcher (auto-setup wrapper)
- **src/bin_xray.py** - Core application (2000+ lines)
  - BinaryParser class - ELF/binary analysis
  - MapFileParser class - Linker map parsing
  - LibraryParser class - Library analysis
  - DependencyGraphBuilder class - Graph construction
  - BinXrayGUI class - Tkinter GUI

### Installation & Testing
- **requirements.txt** - Python dependencies
- **install.sh** - Automated installation script
- **test_installation.py** - Installation verification

### Examples & Documentation
- **examples.py** - 5 complete usage examples
- **README.md** - Main documentation (400+ lines)
- **QUICKSTART.md** - Getting started guide
- **TOOLS_REFERENCE.md** - Tools documentation
- **SDK_EXTENSIONS.md** - Customization guide
- **ALTERNATIVES.md** - Framework alternatives
- **PROJECT_SUMMARY.md** - Project overview

### Project Files
- **.gitignore** - Git ignore rules
- **LICENSE** - MIT License

## 🎓 Learning Path

### Beginner
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `./test_installation.py`
3. Analyze a sample binary
4. Try different layouts

### Intermediate
1. Read [README.md](README.md) fully
2. Configure SDK-specific tools
3. Work with map files
4. Use search/filter features
5. Export graphs

### Advanced
1. Read [SDK_EXTENSIONS.md](SDK_EXTENSIONS.md)
2. Add custom map format parser
3. Study [examples.py](examples.py)
4. Integrate into build system
5. Consider [ALTERNATIVES.md](ALTERNATIVES.md) for scale

## 🔍 Feature Finder

Looking for a specific feature? Here's where to find it:

| Feature | Documentation |
|---------|--------------|
| Binary format support | [README.md - Features](README.md#features) |
| Map file formats | [SDK_EXTENSIONS.md](SDK_EXTENSIONS.md) |
| Graph layouts | [README.md - Visualization](README.md#interactive-visualization) |
| Export formats | [README.md - Export](README.md#export-capabilities) |
| SDK tool setup | [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md) |
| Performance tuning | [ALTERNATIVES.md](ALTERNATIVES.md) |
| Custom parsers | [SDK_EXTENSIONS.md - Custom Formats](SDK_EXTENSIONS.md#custom-map-file-formats) |
| Error messages | [README.md - Troubleshooting](README.md#troubleshooting) |

## 🆘 Getting Help

### Quick Checks
1. Run `./test_installation.py` - Verifies setup
2. Check [README.md - Troubleshooting](README.md#troubleshooting)
3. Review [QUICKSTART.md](QUICKSTART.md) examples

### Common Issues
- **Tools not found** → [TOOLS_REFERENCE.md - Installation](TOOLS_REFERENCE.md#installation-by-platform)
- **Empty graph** → [README.md - Troubleshooting](README.md#troubleshooting)
- **Slow performance** → [ALTERNATIVES.md](ALTERNATIVES.md)
- **Custom SDK** → [SDK_EXTENSIONS.md](SDK_EXTENSIONS.md)

### In-App Help
```
Help menu in application:
  - Required Tools
  - About
```

## 📊 Documentation Statistics

- **Total documentation**: ~3,500 lines across 6 files
- **Code**: ~2,400 lines (src/bin_xray.py + run.py + examples + tests)
- **Total project**: ~6,000 lines
- **File count**: 26+ files

## 🎯 Common Use Cases

### Debugging Binary Bloat
1. Load binary + map file
2. Analyze dependencies
3. Identify large unused libraries
→ See [QUICKSTART.md - Sample Workflow](QUICKSTART.md#sample-workflow)

### Understanding SDK Dependencies
1. Configure SDK tools path
2. Load application binary
3. Graph shows actual dependencies
→ See [SDK_EXTENSIONS.md - TI Jacinto](SDK_EXTENSIONS.md#ti-processor-sdk)

### License Compliance Check
1. Load with library directory
2. Export graph
3. Review linked libraries
→ See [README.md - Export](README.md#export-capabilities)

### Symbol Conflict Resolution
1. Load map file with --cref
2. Search for symbol
3. View all references
→ See [examples.py - Graph Filtering](examples.py)

## 🚦 System Requirements

**Minimum**: Python 3.7+, 512 MB RAM, binutils  
**Recommended**: Python 3.9+, 2 GB RAM, SSD

See [PROJECT_SUMMARY.md - Requirements](PROJECT_SUMMARY.md#system-requirements)

## 📞 Support Channels

- **Documentation**: All .md files in this directory
- **Examples**: [examples.py](examples.py)
- **Tests**: [test_installation.py](test_installation.py)
- **In-app**: Help menu

## 🎉 Ready to Start!

Choose your path:
- **New user?** → Start with [QUICKSTART.md](QUICKSTART.md)
- **Technical user?** → Read [README.md](README.md)
- **SDK developer?** → See [SDK_EXTENSIONS.md](SDK_EXTENSIONS.md)
- **Performance focus?** → Check [ALTERNATIVES.md](ALTERNATIVES.md)

---

**Last Updated**: 2026-02-11  
**Version**: 1.0  
**Total Files**: 13  
**Total Lines**: ~5,000
