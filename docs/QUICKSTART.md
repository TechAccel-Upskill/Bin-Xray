# Bin-Xray Quick Start Guide

Get started with Bin-Xray in 5 minutes!

## Installation

### 1. Quick Install (Ubuntu/Debian)

```bash
cd Bin-xray

# Install system dependencies and Python packages
./install.sh

# Or manually:
sudo apt-get install binutils file python3-tk
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python3 scripts/test_installation.py
```

You should see all tests passing ✓

## First Analysis

### Example 1: Simple ELF Binary

```bash
# Run the GUI
python3 run.py
```

In the GUI:
1. Click "Browse..." next to Binary
2. Select your `.elf` or `.out` file
3. Click "Analyze & Generate Graph"
4. View the dependency graph!

### Example 2: With Map File

For better results, include the linker map file:

1. Binary: `your_app.elf`
2. Map File: `your_app.map`
3. Click "Analyze & Generate Graph"

### Example 3: Complete Analysis

For full dependency analysis:

1. Binary: `/path/to/app.elf`
2. Map File: `/path/to/app.map`
3. Library Dir: `/path/to/libs/`
4. SDK Tools: `/opt/ti/cgt-armllvm/bin/` (if using cross-compiler)
5. Max Depth: `5`
6. Layout: `spring` or `kamada_kawai`
7. Click "Analyze & Generate Graph"

## Common Workflows

### Analyzing a TI Jacinto Project

```
Binary:     vision_apps/out/J7/A72/LINUX/Release/vx_app.out
Map:        vision_apps/out/J7/A72/LINUX/Release/vx_app.map
Libraries:  vision_apps/out/J7/A72/LINUX/Release/lib/
SDK Tools:  /opt/ti/ti-cgt-armllvm_2.1.0.LTS/bin/
```

### Analyzing an ARM Cortex-M Project

```
Binary:     build/firmware.elf
Map:        build/firmware.map
Libraries:  build/libs/
SDK Tools:  /opt/gcc-arm-none-eabi/bin/
```

## Understanding the Graph

### Node Colors

- 🔴 **Red** = Main executable
- 🔵 **Blue** = Static library (.a)
- 🟢 **Teal** = Shared library (.so)
- 🟡 **Light Green** = Object file (.o)

### Edges (Arrows)

- **Solid Red** = Dynamic linking dependency
- **Dashed Green** = Symbol reference
- **Dotted Gray** = Contains relationship

### Interacting with the Graph

- **Zoom**: Mouse wheel or toolbar buttons
- **Pan**: Click and drag
- **Reset**: View → Reset Zoom
- **Filter**: Enter search term and click Apply
- **Details**: View → Show Node Details

## Exporting Results

### Save as Image

```
File → Export Graph (PNG)  # For documentation
File → Export Graph (SVG)  # For publications
```

### Export for Further Analysis

```
File → Export GraphML  # Open in Gephi, Cytoscape, etc.
```

## Tips for Better Results

### 1. Enable Cross-References in Linker

For GNU ld:
```makefile
LDFLAGS += -Wl,--cref
```

For TI linker:
```
--map_file=output.map
--xml_link_info=output.xml
```

### 2. Keep Debug Symbols

Don't strip binaries before analysis:
```makefile
# Good - keeps symbols
STRIP = 

# Bad - removes symbols
STRIP = arm-none-eabi-strip
```

### 3. Filter Large Graphs

If graph has too many nodes:
1. Reduce "Max Depth" to 3-4
2. Use search filter for specific modules
3. Analyze subsystems separately

### 4. Use Hierarchical Layout

For large, structured projects:
- Layout: `hierarchical` (requires pygraphviz)
- Shows clear dependency layers

## Troubleshooting

### "No graph data to visualize"

**Fix**: Ensure at least one of Binary or Map File is provided and exists

### Graph is empty

**Fix**: Check that:
- Binary is an ELF file (run `file your_binary.elf`)
- Map file is text format (open in text editor)
- SDK Tools path points to `bin/` directory

### Tools not found

**Fix**: 
```bash
# Check if tools are installed
which readelf nm objdump

# If not found, install binutils
sudo apt-get install binutils
```

### Symbols missing

**Fix**:
- Don't strip the binary
- Ensure map file was generated with `--cref` flag
- Specify SDK Tools path for cross-compiled binaries

## Advanced Usage

### Programmatic Analysis

```python
from bin_xray import BinaryParser, MapFileParser, DependencyGraphBuilder

# Parse binary
parser = BinaryParser()
binary_info = parser.parse_binary('/path/to/app.elf')

# Parse map
map_parser = MapFileParser()
map_info = map_parser.parse_map_file('/path/to/app.map')

# Build graph
builder = DependencyGraphBuilder()
graph = builder.build_graph(binary_info, map_info)

# Analyze
print(f"Nodes: {graph.number_of_nodes()}")
print(f"Edges: {graph.number_of_edges()}")

# Export
import networkx as nx
nx.write_graphml(graph, 'output.graphml')
```

For more advanced usage, see `README.md` and `SDK_EXTENSIONS.md`.

### Custom SDK Support

See `SDK_EXTENSIONS.md` for how to add support for your SDK's specific linker format.

### Alternative Frameworks

See `ALTERNATIVES.md` for options if you need better performance for very large graphs.

## Configuration

Bin-Xray remembers your last used paths in `~/.binxray_config.json`:

```json
{
  "last_binary": "/path/to/last/binary.elf",
  "last_map": "/path/to/last/map.map",
  "last_lib_dir": "/path/to/libs",
  "last_sdk_tools": "/opt/ti/bin",
  "graph_depth": 5,
  "layout_algorithm": "spring"
}
```

You can edit this file manually or delete it to reset.

## Getting Help

### Documentation

- `README.md` - Full documentation
- `TOOLS_REFERENCE.md` - System tools setup
- `SDK_EXTENSIONS.md` - SDK-specific configuration
- `ALTERNATIVES.md` - Alternative frameworks

### In-App Help

```
Help → Required Tools  # List of system tools needed
Help → About          # Version information
```

### Common Issues

**Issue**: Graph too large to see
- **Solution**: Use filter or reduce max depth

**Issue**: Layout looks messy
- **Solution**: Try different layout algorithm (kamada_kawai often works better)

**Issue**: Wrong toolchain detected
- **Solution**: Explicitly specify SDK Tools path

## Next Steps

1. ✅ Analyze your first binary
2. ✅ Try filtering to find specific dependencies
3. ✅ Export graph for documentation
4. 📖 Read `SDK_EXTENSIONS.md` for your specific SDK
5. 🔧 Configure your build to generate better map files
6. 🚀 Integrate into your CI/CD pipeline

## Sample Workflow

Here's a complete example workflow:

```bash
# 1. Build your project with map file generation
make clean
make MAP=1

# 2. Run Bin-Xray
python3 run.py

# 3. Load files:
#    Binary: build/output.elf
#    Map: build/output.map
#    Libraries: build/libs/

# 4. Analyze (Max Depth: 5, Layout: spring)

# 5. Filter for specific module (e.g., "driver")

# 6. Export result:
#    File → Export Graph (PNG)
#    Save as: docs/dependency_graph.png

# 7. Export for detailed analysis:
#    File → Export GraphML
#    Save as: analysis/deps.graphml
#    Open in Gephi for further exploration
```

## Resources

- **NetworkX Documentation**: https://networkx.org/documentation/stable/
- **Graphviz Layouts**: https://graphviz.org/docs/layouts/
- **ELF Format**: https://refspecs.linuxfoundation.org/elf/
- **GNU Binutils**: https://sourceware.org/binutils/docs/

---

**Happy analyzing!** 🔍

For issues or questions, check the main `README.md` and the docs in this folder.
