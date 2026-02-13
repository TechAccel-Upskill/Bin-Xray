# Bin-Xray: Binary Dependency Analyzer for Embedded Systems

A comprehensive Python GUI tool for visualizing and analyzing dependency relationships in SDK build outputs, especially for automotive/ADAS embedded systems (TI Jacinto, NXP, Qualcomm, etc.).

![Bin-Xray GUI](docs/screenshot.png)

## Features

✅ **Binary Analysis**
- Parse ELF, .out, .axf, .bin executables
- Extract dynamic dependencies (DT_NEEDED)
- Analyze imported/exported symbols
- Support for stripped and non-stripped binaries

✅ **Symbol-Level Dependency Visualization** 🆕
- See which specific functions/variables are referenced between modules
- Visualize undefined symbols (needs) and defined symbols (provides)
- Match symbol dependencies across object files and libraries
- Example: `main.o --[vector_magnitude]--> utils.o`
- Toggle between library-level and symbol-level views

✅ **Linker Map File Parsing**
- GNU ld map files
- TI linker map files (TMS320, Jacinto SDK)
- ARM linker maps
- Cross-reference table analysis (`--cref`)
- Memory region mapping
- Section placement analysis

✅ **Library Analysis**
- Static archives (.a)
- Shared objects (.so, .dll)
- Object files (.o)
- Symbol extraction from libraries
- Recursive dependency tracking

✅ **Interactive Visualization**
- NetworkX-based dependency graphs
- Matplotlib integration
- Multiple layout algorithms (spring, kamada-kawai, hierarchical, etc.)
- Color-coded node types and edge types
- Symbol names shown as edge labels
- Zoom, pan, and reset controls
- Search/filter nodes

✅ **Export Capabilities**
- PNG/SVG image export
- GraphML format for external tools
- Node details view

## Installation

### Prerequisites

**Python 3.7+** with the following packages:

```bash
pip install networkx matplotlib
```

**System Tools** (for binary analysis):
- `readelf` - Read ELF file information
- `nm` - List symbols from object files  
- `objdump` - Display object file information
- `ar` - Archive utility (for .a files)
- `file` - Determine file type

Install on Ubuntu/Debian:
```bash
sudo apt-get install binutils file python3-tk
```

Install on Fedora/RHEL:
```bash
sudo dnf install binutils file python3-tkinter
```

Install on macOS:
```bash
brew install binutils
```

### Quick Start

1. Clone or download this repository
2. Run the application:
   ```bash
   python3 run.py
   ```

## User Guide

### Run an Analysis

1. Open the app and select:
   - Binary file (.elf, .out, .axf)
   - Map file (.map, optional but recommended)
   - Library directory (optional, for .a/.so)
2. Click "Generate Report".
3. Wait for the analysis to finish; the report appears in the right panel.

### Copy Report Text

- Highlight the text in the report panel and press `Ctrl+C`.
- Or use the "Copy" button in the report toolbar to copy the full report.

### Understand the Report

The report is organized as follows:

- Build score header and usage ratio.
- Detailed Summary of unused resources of <binary>.
- Static libraries section with used/not used counts and itemized libraries/objects.
- Dynamic libraries section with used/not used counts.
- Recommendations with cleanup tips.
- Legend for used vs not used markers.

### Common Tasks

- Reduce clutter: lower max depth to 3-4.
- Focus on a subsystem: use the search box.
- Export the report: click "Export" to save the text report.

## Usage

### Basic Workflow

1. **Select Input Files**
   - **Binary**: The main executable (.elf, .out, .axf, etc.)
   - **Map File**: Linker-generated map file (.map)
   - **Library Dir**: Directory containing .a or .so libraries
   - **SDK Tools** (optional): Path to SDK-specific toolchain

2. **Configure Options**
   - **Max Depth**: Control graph complexity (1-10)
   - **Layout**: Choose visualization algorithm

3. **Analyze**
   - Click "Analyze & Generate Graph"
   - Wait for parsing and graph generation
   - Interact with the visualization

4. **Export**
   - File → Export Graph (PNG/SVG)
   - File → Export GraphML

### Example: TI Jacinto TDA4VM SDK

```bash
# Typical file locations after build
Binary:     /path/to/sdk/vision_apps/out/J7/A72/LINUX/Release/vx_app_arm_remote_log.out
Map File:   /path/to/sdk/vision_apps/out/J7/A72/LINUX/Release/vx_app_arm_remote_log.map
Library Dir: /path/to/sdk/vision_apps/out/J7/A72/LINUX/Release/lib/
SDK Tools:   /path/to/ti-cgt-armllvm_2.1.0.LTS/bin/
```

### Search & Filter

Use the search box to filter nodes by name:
- Enter partial name (e.g., "libvision" to find vision-related libraries)
- Press Enter or click "Apply"
- Click "Reset" to show full graph

### Node Details

Click "View → Show Node Details" to see:
- Node type (binary, library, object file)
- File paths
- Symbol counts
- Dependency counts

## Understanding the Graph

### Node Colors

- 🔴 **Red**: Main executable binary
- 🔵 **Blue**: Static library (.a)
- 🟢 **Teal**: Shared library (.so)
- 🟡 **Light Green**: Object file (.o)
- ⚪ **Gray**: Unknown/unresolved

### Edge Types

- **Solid Red**: Dynamic dependency (DT_NEEDED)
- **Dashed Green**: Symbol reference
- **Dotted Gray**: Library contains object

## SDK-Specific Extensions

### TI Processor SDK (Jacinto TDA4VM)

TI map files have unique format quirks:

```python
# The parser handles TI-specific sections:
# - OUTPUT SECTION instead of Memory Configuration
# - GLOBAL SYMBOLS table format
# - .obj extension instead of .o
```

**TI Toolchain Detection**: If you specify SDK tools path with TI tools (e.g., `/ti-cgt-armllvm_2.1.0.LTS/bin/`), the parser will automatically detect and use:
- `tiarm-readelf`
- `tiarm-nm`
- `tiarm-objdump`

### NXP S32K SDK

For NXP automotive SDKs:

```bash
Binary:     application.elf
Map File:   application.map  
SDK Tools:  /opt/NXP/S32DS_ARM_v2.2/S32DS/build_tools/gcc-6.3-arm32-eabi/bin/
```

The tool will use `arm-none-eabi-` prefixed tools.

### Qualcomm Hexagon SDK

For Qualcomm SNPE/Hexagon DSP:

```bash
Binary:     libsnpe.so
SDK Tools:  /opt/qualcomm/hexagon/tools/HEXAGON_Tools/8.x/Tools/bin/
```

Use `hexagon-` prefixed tools.

## Extending the Parser

### Adding Custom Map Format Support

Edit `MapFileParser._detect_format()` and add a new parser method:

```python
def _parse_custom_map(self, content: str, info: MapFileInfo):
    """Parse custom vendor map file format."""
    lines = content.splitlines()
    
    for line in lines:
        # Your parsing logic here
        if 'CUSTOM_SECTION' in line:
            # Extract section information
            pass
```

### Supporting New Binary Formats

Extend `BinaryParser` to handle new formats:

```python
def _parse_custom_format(self, binary_path: str) -> BinaryInfo:
    """Parse vendor-specific binary format."""
    info = BinaryInfo(path=binary_path, name=os.path.basename(binary_path))
    
    # Use vendor-specific tools
    # ...
    
    return info
```

## Performance Tips

### For Large Projects

1. **Limit Depth**: Set max depth to 3-4 for initial exploration
2. **Filter Libraries**: Only include relevant library directories
3. **Use Hierarchical Layout**: Better for large graphs (requires pygraphviz)
4. **Filter by Search**: Focus on specific subsystems

### Memory Optimization

The map parser reads files line-by-line to avoid loading entire map into memory. For extremely large files (>100MB), consider:

```python
# Stream processing in chunks
CHUNK_SIZE = 100000  # lines
```

## Alternative Frameworks (for Advanced Users)

If Tkinter+Matplotlib becomes too slow for very large graphs (>1000 nodes), consider:

### PyQt + PyGraphviz

```bash
pip install PyQt5 pygraphviz
```

**Advantages**:
- Native graphviz rendering (faster for large graphs)
- Better performance
- More professional UI widgets

**Disadvantages**:
- Requires Qt installation
- More complex deployment

### Dear PyGui

```bash
pip install dearpygui
```

**Advantages**:
- GPU-accelerated rendering
- Very fast for large datasets
- Modern UI

**Disadvantages**:
- Different API paradigm
- Less mature ecosystem

### Plotly Dash (Web-based)

```bash
pip install dash plotly
```

**Advantages**:
- Interactive web-based
- Can share via URL
- Advanced filtering

**Disadvantages**:
- Requires web server
- More complex setup

## Troubleshooting

### "Tool 'readelf' not found"

Install binutils:
```bash
sudo apt-get install binutils   # Ubuntu/Debian
sudo dnf install binutils        # Fedora/RHEL
brew install binutils            # macOS
```

### "No graph data to visualize"

Ensure you've provided at least one of:
- A valid binary file (.elf, .out, etc.)
- A valid map file (.map)

### Graph is too cluttered

Try:
1. Reduce max depth to 3-4
2. Use hierarchical layout
3. Filter nodes using search
4. Focus on specific subsystems

### Symbols not showing

For stripped binaries, the map file becomes essential. Ensure:
- Map file was generated with `--cref` flag (GNU ld)
- Map file is from the same build as binary

### SDK tools not detected

Specify the **bin** directory containing executables, not the SDK root:
- ✅ `/opt/ti/cgt-armllvm/bin/`
- ❌ `/opt/ti/cgt-armllvm/`

## System Tools Reference

### Required for ELF Analysis

| Tool | Purpose | Alternative |
|------|---------|-------------|
| `readelf` | ELF headers, sections, dynamics | `objdump -h` |
| `nm` | Symbol tables | `readelf -s` |
| `objdump` | Disassembly, sections | `readelf` |
| `ar` | Static archive extraction | `nm --print-armap` |
| `file` | File type detection | manual detection |

### SDK-Specific Tool Prefixes

| SDK/Toolchain | Prefix | Example |
|---------------|--------|---------|
| TI ARM Clang | `tiarm-` | `tiarm-readelf` |
| ARM GCC | `arm-none-eabi-` | `arm-none-eabi-nm` |
| AArch64 | `aarch64-linux-gnu-` | `aarch64-linux-gnu-objdump` |
| RISC-V | `riscv64-unknown-elf-` | `riscv64-unknown-elf-nm` |
| Hexagon | `hexagon-` | `hexagon-nm` |

## Configuration

Settings are saved to `~/.binxray_config.json`:

```json
{
  "last_binary": "/path/to/app.elf",
  "last_map": "/path/to/app.map",
  "last_lib_dir": "/path/to/libs",
  "last_sdk_tools": "/path/to/sdk/bin",
  "graph_depth": 5,
  "layout_algorithm": "spring"
}
```

## Architecture

```
run.py (launcher) → src/bin_xray.py (core)
├── Data Structures
│   ├── Symbol
│   ├── BinaryInfo
│   └── MapFileInfo
├── Parsers
│   ├── BinaryParser (ELF, PE, Mach-O)
│   ├── MapFileParser (GNU ld, TI, ARM, IAR)
│   └── LibraryParser (.a, .so)
├── Graph Builder
│   └── DependencyGraphBuilder (NetworkX)
└── GUI
    └── BinXrayGUI (Tkinter)
```

## Contributing

Contributions welcome! Areas for improvement:

- [x] Symbol-level dependency visualization
- [ ] Support for more linker formats (IAR, Keil)
- [ ] PE/COFF file support (Windows embedded)
- [ ] Interactive node clicking for symbol details
- [ ] Diff mode (compare two builds)
- [ ] Integration with build systems (CMake, Make)
- [ ] Plugin system for custom parsers

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step getting started guide
- **[SYMBOL_VISUALIZATION.md](SYMBOL_VISUALIZATION.md)** - Symbol-level dependency analysis 🆕
- **[SDK_EXTENSIONS.md](SDK_EXTENSIONS.md)** - SDK-specific configurations
- **[TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)** - Binary analysis tools guide
- **[ALTERNATIVES.md](ALTERNATIVES.md)** - Comparison with other tools
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Architecture overview

## License

MIT License - feel free to use in commercial and open-source projects.

## FAQ

**Q: Does this work with stripped binaries?**  
A: Yes, but you'll need the map file for symbol information.

**Q: Can I analyze Windows .exe files?**  
A: Basic support exists, but full PE analysis is not implemented. Consider using Windows-specific tools like `dumpbin`.

**Q: How do I analyze Yocto/Buildroot outputs?**  
A: Point to the final image's staging directory for libraries, and use the cross-toolchain path for SDK tools.

**Q: Can I use this with Bazel builds?**  
A: Yes, extract the binary and map from `bazel-bin/` and analyze normally.

**Q: Does it work on macOS?**  
A: Yes, though some GNU tools may need installation via Homebrew. Mach-O support is basic.

## Support

For issues, questions, or feature requests:
- Check the troubleshooting section
- Review the examples for your SDK type
- Examine the parser output in terminal for debugging

## Acknowledgments

Built with:
- [NetworkX](https://networkx.org/) - Graph analysis
- [Matplotlib](https://matplotlib.org/) - Visualization
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework
