# Test Binaries for Bin-Xray

## Available Test Files

### 1. **embedded_app.elf** - Custom Compiled Embedded Application
- **Type**: ELF 64-bit executable (x86-64)
- **Source**: embedded_app.c (included)
- **Map File**: embedded_app.map (437 KB - includes cross-references)
- **Features**: 
  - Multiple functions (init_hardware, init_drivers, process_data)
  - Links to libm (math library)
  - Contains debug symbols
  - Real linker map with --cref enabled
- **Best for**: Testing map file parsing and symbol cross-references

### 2. **system_ls.elf** - Real GNU ls Command
- **Type**: ELF 64-bit executable (stripped)
- **Source**: Copy of /bin/ls
- **Size**: 135 KB
- **Features**:
  - Real-world system binary
  - Multiple dynamic dependencies (libc, libselinux, libpcre2, etc.)
  - Stripped binary (good for testing without symbols)
- **Best for**: Testing dynamic dependency analysis

### 3. **system_bash.elf** - Real GNU Bash Shell
- **Type**: ELF 64-bit executable (stripped)
- **Source**: Copy of /bin/bash
- **Size**: 1.4 MB
- **Features**:
  - Large, complex binary
  - Many dynamic dependencies
  - Extensive symbol table
- **Best for**: Testing performance with larger binaries

### 4. **libs/** - Real System Libraries
- libc.so.6 - Standard C library
- libm.so.6 - Math library
- **Best for**: Testing library dependency analysis

## How to Use in Bin-Xray GUI

### Test 1: Simple Analysis (Recommended First)
```
1. Launch Bin-Xray GUI
2. Click Browse next to "Binary"
3. Navigate to: ~/Working/Bin-xray/test_binaries/
4. Select: embedded_app.elf
5. Click "Analyze & Generate Graph"
```

**You should see:**
- Red node for embedded_app.elf
- Teal nodes for libc.so.6, libm.so.6, ld-linux-x86-64.so.2
- Arrows showing dependencies

### Test 2: With Map File (Full Analysis)
```
1. Binary: embedded_app.elf
2. Map File: embedded_app.map
3. Click "Analyze & Generate Graph"
```

**You should see:**
- More detailed node information
- Object file references (.o files)
- Symbol cross-references
- Section information

### Test 3: With Libraries
```
1. Binary: embedded_app.elf
2. Map File: embedded_app.map
3. Library Dir: libs/
4. Click "Analyze & Generate Graph"
```

**You should see:**
- Library nodes analyzed
- Symbols from libraries
- Full dependency chain

### Test 4: Larger Binary
```
1. Binary: system_bash.elf
2. Max Depth: 3 (to keep it manageable)
3. Layout: kamada_kawai
4. Click "Analyze & Generate Graph"
```

**You should see:**
- Complex dependency graph
- Many shared libraries
- Good test of visualization performance

## Expected Results

### embedded_app.elf Analysis
- **Dynamic Dependencies**: 3-4 libraries (libc, libm, ld-linux)
- **Sections**: .text, .data, .bss, .rodata, etc.
- **Symbols**: init_hardware, init_drivers, process_data, calculate_value, main
- **Graph Nodes**: 4-6 nodes
- **Graph Edges**: 3-5 edges

### system_ls.elf Analysis  
- **Dynamic Dependencies**: 8-10 libraries
- **Graph Nodes**: 10-12 nodes
- **Graph Edges**: 10-15 edges

### system_bash.elf Analysis
- **Dynamic Dependencies**: 10-15 libraries
- **Graph Nodes**: 15-20 nodes
- **Graph Edges**: 20-30 edges

## Verification

Check that binaries are valid:
```bash
file *.elf
readelf -h embedded_app.elf
nm embedded_app.elf | head
readelf -d embedded_app.elf
```

Check map file:
```bash
grep "Cross Reference" embedded_app.map
head -100 embedded_app.map
```

## Tips

1. **Start small**: Use embedded_app.elf first
2. **Try different layouts**: spring, kamada_kawai, circular
3. **Use filter**: Search for "libm" or "init" to filter nodes
4. **Export**: Try File → Export Graph (PNG) to save visualization
5. **Compare**: Analyze with and without map file to see difference

## Source Code

The embedded_app.c source is included for reference. It simulates a typical embedded application with:
- Hardware initialization
- Driver initialization  
- Data processing
- Mathematical calculations

You can modify and recompile:
```bash
gcc -o embedded_app.elf embedded_app.c -lm -Wl,-Map=embedded_app.map,--cref -g
```

---

**All binaries are real ELF files from actual compilation or system binaries - no dummy files!**
