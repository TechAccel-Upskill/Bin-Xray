# Extending Bin-Xray for Specific SDKs

This guide shows how to extend Bin-Xray to handle SDK-specific quirks and formats.

## Table of Contents

1. [TI Processor SDK (Jacinto TDA4VM)](#ti-processor-sdk)
2. [NXP S32K SDK](#nxp-s32k-sdk)
3. [Qualcomm Hexagon/SNPE](#qualcomm-hexagon)
4. [Custom Map File Formats](#custom-map-formats)
5. [Adding New Binary Tools](#adding-binary-tools)

---

## TI Processor SDK (Jacinto TDA4VM) {#ti-processor-sdk}

### Map File Format Specifics

TI linker (tiarmclang) produces map files with unique characteristics:

**Key Differences from GNU ld:**
- Uses `OUTPUT SECTION` instead of `Memory Configuration`
- Object files have `.obj` extension instead of `.o`
- Different cross-reference table format
- Memory regions defined in linker command file (.cmd)

### Example TI Map File Structure

```
******************************************************************************
          TMS320C2000 Linker PC v20.2.1
******************************************************************************

OUTPUT SECTION                    ORIGIN       LENGTH
--------------------            --------     --------
.text                           0x00000000   0x00012340
  .text:_c_int00                0x00000000   0x00000020   main.obj
  .text:main                    0x00000020   0x00000100   main.obj
  .text:foo                     0x00000120   0x00000050   lib.obj

.data                           0x80000000   0x00001000
  .data:global_var              0x80000000   0x00000004   main.obj
```

### Extending the Parser

Add TI-specific parsing in `MapFileParser._parse_ti_map()`:

```python
def _parse_ti_map_extended(self, content: str, info: MapFileInfo):
    """Extended TI map parser with Jacinto SDK specifics."""
    lines = content.splitlines()
    
    current_section = None
    
    for i, line in enumerate(lines):
        # Parse OUTPUT SECTION header
        if 'OUTPUT SECTION' in line:
            # Next lines are section definitions
            continue
        
        # Parse section with address and size
        # Format: .text    0x00000000   0x12345
        match = re.match(r'^(\.[\w.]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)', 
                        line, re.IGNORECASE)
        if match:
            section, addr, size = match.groups()
            current_section = section
            if section not in info.section_map:
                info.section_map[section] = []
            continue
        
        # Parse object file contributions
        # Format:   .text:_c_int00   0x00000000   0x00000020   main.obj
        if current_section:
            obj_match = re.match(
                r'\s+(\.[\w.:]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+(\S+\.obj)',
                line, re.IGNORECASE
            )
            if obj_match:
                subsection, addr, size, obj_file = obj_match.groups()
                if obj_file not in info.section_map[current_section]:
                    info.section_map[current_section].append(obj_file)
        
        # Parse GLOBAL SYMBOLS section (TI-specific)
        if 'GLOBAL SYMBOLS' in line:
            self._parse_ti_global_symbols(lines[i:], info)
```

### TI Toolchain Detection

Ensure `BinaryParser` detects TI tools:

```python
def _detect_tools(self):
    """Enhanced tool detection for TI toolchains."""
    # ... existing code ...
    
    if self.sdk_tools_path:
        # TI-specific prefixes
        ti_prefixes = ['tiarm-', 'cl2000-', 'cl470-', '']
        
        for prefix in ti_prefixes:
            tiarm_readelf = os.path.join(self.sdk_tools_path, 
                                        f"{prefix}readelf")
            if os.path.exists(tiarm_readelf):
                self.tools['readelf'] = tiarm_readelf
                self.tool_prefix = prefix
                break
```

### Usage Example

```bash
# TI Jacinto TDA4VM project structure
Binary:     vision_apps/out/J7/A72/LINUX/Release/app.out
Map:        vision_apps/out/J7/A72/LINUX/Release/app.map
Libraries:  vision_apps/out/J7/A72/LINUX/Release/lib/
SDK Tools:  /opt/ti/ti-cgt-armllvm_2.1.0.LTS/bin/
```

---

## NXP S32K SDK {#nxp-s32k-sdk}

### SDK Structure

NXP S32 Design Studio uses ARM GCC toolchain with specific naming:

```
S32K SDK Structure:
├── build/
│   ├── gcc/
│   │   ├── application.elf
│   │   ├── application.map
│   │   └── lib/
├── SDK/
│   └── platform/
│       └── drivers/
└── toolchain/
    └── gcc-arm-none-eabi/
```

### Map File Specifics

NXP uses standard GNU ld with custom linker scripts (`.ld` files):

```ld
/* Memory Regions */
MEMORY
{
  m_interrupts  : ORIGIN = 0x00000000, LENGTH = 0x00000400
  m_text        : ORIGIN = 0x00000400, LENGTH = 0x0007FC00
  m_data        : ORIGIN = 0x1FFF0000, LENGTH = 0x00010000
}
```

### Extending for NXP

Add memory region parsing for NXP-specific names:

```python
def _parse_nxp_memory_regions(self, content: str, info: MapFileInfo):
    """Parse NXP S32K specific memory regions."""
    
    # NXP-specific region names
    nxp_regions = {
        'm_interrupts': 'Interrupt Vectors',
        'm_text': 'Code (Flash)',
        'm_data': 'Data (RAM)',
        'm_data_2': 'Data RAM Bank 2',
        'm_flash_config': 'Flash Configuration'
    }
    
    in_memory = False
    for line in content.splitlines():
        if 'MEMORY' in line or 'Memory Configuration' in line:
            in_memory = True
            continue
        
        if in_memory and line.strip() == '':
            in_memory = False
        
        if in_memory:
            for region_name, description in nxp_regions.items():
                if region_name in line:
                    match = re.search(
                        r'(0x[0-9a-f]+)\s+(0x[0-9a-f]+)', 
                        line, re.IGNORECASE
                    )
                    if match:
                        origin, length = match.groups()
                        info.memory_regions[region_name] = {
                            'origin': int(origin, 16),
                            'length': int(length, 16),
                            'description': description
                        }
```

### Driver Symbol Detection

NXP drivers have consistent naming patterns:

```python
def identify_nxp_modules(self, symbol_name: str) -> str:
    """Identify NXP SDK module from symbol name."""
    
    nxp_prefixes = {
        'LPSPI_': 'SPI Driver',
        'LPUART_': 'UART Driver',
        'FLEXCAN_': 'CAN Driver',
        'ADC_': 'ADC Driver',
        'FTM_': 'Timer Driver',
        'CLOCK_': 'Clock Manager',
        'POWER_': 'Power Manager'
    }
    
    for prefix, module in nxp_prefixes.items():
        if symbol_name.startswith(prefix):
            return module
    
    return 'Application'
```

---

## Qualcomm Hexagon/SNPE {#qualcomm-hexagon}

### SNPE (Snapdragon Neural Processing Engine)

SNPE uses custom DLC (Deep Learning Container) format alongside standard .so files.

### Hexagon DSP Analysis

```python
class HexagonDSPParser:
    """Parser for Qualcomm Hexagon DSP binaries."""
    
    def __init__(self, sdk_tools_path: str):
        self.hexagon_tools = sdk_tools_path
        # Hexagon tools: hexagon-readelf, hexagon-nm, hexagon-objdump
    
    def parse_hexagon_binary(self, binary_path: str) -> BinaryInfo:
        """Parse Hexagon DSP executable."""
        
        info = BinaryInfo(
            path=binary_path,
            name=os.path.basename(binary_path),
            architecture='Hexagon DSP'
        )
        
        # Use hexagon-specific tools
        hexagon_nm = os.path.join(self.hexagon_tools, 'hexagon-nm')
        
        result = subprocess.run(
            [hexagon_nm, '-C', '--defined-only', binary_path],
            capture_output=True, text=True
        )
        
        # Parse symbols...
        
        return info
```

### SNPE Model Dependencies

```python
def analyze_snpe_model(self, dlc_file: str) -> Dict:
    """Analyze SNPE DLC model dependencies."""
    
    # SNPE models have metadata about layer dependencies
    snpe_info = {
        'model': dlc_file,
        'runtime_deps': [],
        'layers': []
    }
    
    # Use snpe-dlc-info tool if available
    snpe_info_tool = os.path.join(self.sdk_tools_path, 'snpe-dlc-info')
    
    if os.path.exists(snpe_info_tool):
        result = subprocess.run(
            [snpe_info_tool, '-i', dlc_file],
            capture_output=True, text=True
        )
        
        # Parse layer information
        for line in result.stdout.splitlines():
            if 'Layer' in line:
                # Extract layer dependencies
                pass
    
    return snpe_info
```

---

## Custom Map File Formats {#custom-map-formats}

### Adding a New Format

1. **Detect the format** in `_detect_format()`:

```python
def _detect_format(self, content: str) -> str:
    """Detect linker map format."""
    first_lines = '\n'.join(content.splitlines()[:50])
    
    # Add your custom detection
    if 'YOUR_VENDOR_MARKER' in first_lines:
        return 'Custom Vendor'
    
    # ... existing detections ...
    
    return 'Unknown'
```

2. **Create a parser method**:

```python
def _parse_custom_vendor_map(self, content: str, info: MapFileInfo):
    """Parse custom vendor linker map format."""
    
    lines = content.splitlines()
    current_section = None
    
    for line in lines:
        # Example: Parse section headers
        if line.startswith('SECTION:'):
            section_name = line.split(':')[1].strip()
            current_section = section_name
            info.section_map[section_name] = []
        
        # Example: Parse object files
        elif line.startswith('  FILE:'):
            obj_file = line.split(':')[1].strip()
            if current_section:
                info.section_map[current_section].append(obj_file)
        
        # Example: Parse symbols
        elif line.startswith('  SYMBOL:'):
            parts = line.split()
            symbol_name = parts[1]
            defined_in = parts[3] if len(parts) > 3 else 'unknown'
            
            if symbol_name not in info.symbol_xref:
                info.symbol_xref[symbol_name] = {
                    'defined_by': [],
                    'used_by': []
                }
            
            info.symbol_xref[symbol_name]['defined_by'].append(defined_in)
```

3. **Hook it up** in `parse_map_file()`:

```python
def parse_map_file(self, map_path: str) -> MapFileInfo:
    """Parse linker map file."""
    # ... existing code ...
    
    if map_format == 'Custom Vendor':
        self._parse_custom_vendor_map(content, info)
    
    return info
```

---

## Adding New Binary Tools {#adding-binary-tools}

### Supporting Proprietary Analysis Tools

Some SDKs come with proprietary binary analysis tools:

```python
def _detect_proprietary_tools(self):
    """Detect vendor-specific binary tools."""
    
    # Example: Renesas RX toolchain
    if 'renesas' in self.sdk_tools_path.lower():
        tools_map = {
            'readelf': 'rx-elf-readelf',
            'nm': 'rx-elf-nm',
            'objdump': 'rx-elf-objdump'
        }
        
        for tool, vendor_tool in tools_map.items():
            tool_path = os.path.join(self.sdk_tools_path, vendor_tool)
            if os.path.exists(tool_path):
                self.tools[tool] = tool_path
    
    # Example: RISC-V toolchain
    elif 'riscv' in self.sdk_tools_path.lower():
        prefix = 'riscv64-unknown-elf-'
        for tool in ['readelf', 'nm', 'objdump']:
            tool_path = os.path.join(self.sdk_tools_path, f"{prefix}{tool}")
            if os.path.exists(tool_path):
                self.tools[tool] = tool_path
```

### Using Custom Symbol Extraction

```python
def _extract_symbols_custom_tool(self, binary_path: str, 
                                 tool_path: str) -> List[Symbol]:
    """Extract symbols using a custom tool."""
    
    symbols = []
    
    try:
        # Run custom tool
        result = subprocess.run(
            [tool_path, '--symbols', binary_path],
            capture_output=True, text=True, timeout=30
        )
        
        # Parse custom output format
        for line in result.stdout.splitlines():
            # Example format: "SYMBOL_NAME T 0x1000 100 source.o"
            parts = line.split()
            if len(parts) >= 4:
                sym = Symbol(
                    name=parts[0],
                    type=parts[1],
                    address=int(parts[2], 16),
                    size=int(parts[3]),
                    source=parts[4] if len(parts) > 4 else ''
                )
                symbols.append(sym)
    
    except Exception as e:
        print(f"Custom tool error: {e}")
    
    return symbols
```

---

## Testing Your Extension

### Validation Script

```python
def validate_sdk_extension(sdk_name: str, test_files: Dict[str, str]):
    """Validate SDK-specific extension."""
    
    print(f"Testing {sdk_name} extension...")
    
    # Test binary parsing
    if 'binary' in test_files:
        parser = BinaryParser(test_files.get('sdk_tools'))
        info = parser.parse_binary(test_files['binary'])
        
        assert info.architecture != 'Unknown', "Failed to detect architecture"
        assert len(info.defined_symbols) > 0, "No symbols extracted"
        print(f"  ✓ Binary parsing: {len(info.defined_symbols)} symbols")
    
    # Test map parsing
    if 'map' in test_files:
        map_parser = MapFileParser()
        map_info = map_parser.parse_map_file(test_files['map'])
        
        assert len(map_info.section_map) > 0, "No sections found"
        print(f"  ✓ Map parsing: {len(map_info.section_map)} sections")
    
    print(f"{sdk_name} validation complete!\n")

# Run validation
validate_sdk_extension('TI Jacinto', {
    'binary': 'path/to/test.out',
    'map': 'path/to/test.map',
    'sdk_tools': '/opt/ti/cgt-armllvm/bin/'
})
```

---

## Contributing Your Extension

If you've extended Bin-Xray for a new SDK:

1. **Document the format** in this file
2. **Provide test files** (sanitized, if proprietary)
3. **Add detection logic** to the appropriate parser
4. **Include usage examples**
5. **Submit a pull request** (if open-source)

---

## Example: Complete IAR Extension

```python
# Add to MapFileParser class

def _detect_iar_format(self, content: str) -> bool:
    """Detect IAR linker map format."""
    return 'IAR Linker' in content or 'ILINK' in content

def _parse_iar_map(self, content: str, info: MapFileInfo):
    """Parse IAR Embedded Workbench linker map."""
    
    lines = content.splitlines()
    
    in_module_summary = False
    in_entry_list = False
    
    for line in lines:
        # Parse MODULE SUMMARY section
        if 'MODULE SUMMARY' in line:
            in_module_summary = True
            continue
        elif in_module_summary and line.strip() == '':
            in_module_summary = False
        
        if in_module_summary:
            # Format: module.o  123  456  .text
            match = re.match(r'\s*(\S+\.o)\s+(\d+)\s+(\d+)\s+(\.[\w]+)',
                           line)
            if match:
                obj_file, code_size, data_size, section = match.groups()
                
                if section not in info.section_map:
                    info.section_map[section] = []
                info.section_map[section].append(obj_file)
        
        # Parse ENTRY LIST section
        if 'ENTRY LIST' in line:
            in_entry_list = True
            continue
        
        if in_entry_list:
            # Format: symbol_name  0x1234  module.o
            match = re.match(r'\s*(\S+)\s+(0x[0-9a-f]+)\s+(\S+\.o)',
                           line, re.IGNORECASE)
            if match:
                symbol, addr, obj_file = match.groups()
                
                if symbol not in info.symbol_xref:
                    info.symbol_xref[symbol] = {
                        'defined_by': [],
                        'used_by': []
                    }
                info.symbol_xref[symbol]['defined_by'].append(obj_file)

# Hook it up
def parse_map_file(self, map_path: str) -> MapFileInfo:
    # ... existing code ...
    
    if self._detect_iar_format(content):
        self._parse_iar_map(content, info)
    
    return info
```

Use it:
```python
# IAR ARM project
Binary:     Output/Debug/Exe/project.out
Map:        Output/Debug/List/project.map
SDK Tools:  C:/IAR/EWARM/arm/bin/
```

---

## Summary

Extending Bin-Xray for your SDK:

1. **Identify unique characteristics** of your linker map format
2. **Add detection logic** to recognize the format
3. **Implement parsing** for sections, symbols, and memory regions
4. **Configure tool paths** for SDK-specific binutils
5. **Test thoroughly** with real project outputs
6. **Document** the extension for other users

Happy analyzing! 🔍
