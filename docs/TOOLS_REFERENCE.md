# System Tools Reference for Bin-Xray

This document details all external system tools used by Bin-Xray and how to configure SDK-specific versions.

## Required Tools

### Core Binary Analysis Tools

| Tool | Purpose | Required | Alternative |
|------|---------|----------|-------------|
| **readelf** | Read ELF headers, sections, dynamic dependencies | Yes (for ELF) | objdump |
| **nm** | Extract symbol tables | Yes | readelf -s |
| **objdump** | Disassembly and object file info | No | readelf |
| **ar** | Extract archive members from .a files | Yes (for .a) | - |
| **file** | Detect file type and architecture | Recommended | manual detection |
| **ldd** | List shared library dependencies | Optional | readelf -d |

## Installation by Platform

### Ubuntu / Debian

```bash
# Install all required tools
sudo apt-get update
sudo apt-get install -y binutils file

# Verify installation
readelf --version
nm --version
ar --version
file --version
```

### Fedora / RHEL / CentOS

```bash
# Install tools
sudo dnf install -y binutils file

# Or for older systems
sudo yum install -y binutils file
```

### macOS

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install binutils
brew install binutils

# Note: macOS tools may have 'g' prefix (gnm, gobjdump, etc.)
```

### Windows (WSL)

```bash
# Use Windows Subsystem for Linux (WSL)
# Then follow Ubuntu/Debian instructions

# Or use MinGW
# Download from: https://sourceforge.net/projects/mingw-w64/
```

## SDK-Specific Toolchains

### TI (Texas Instruments)

**TI ARM Clang Compiler Tools**

```bash
# Download from: https://www.ti.com/tool/ARM-CGT
# Typical installation: /opt/ti/ti-cgt-armllvm_X.X.X.LTS/

# Tools location
SDK_TOOLS=/opt/ti/ti-cgt-armllvm_2.1.0.LTS/bin/

# Available tools:
tiarm-readelf      # ELF reader
tiarm-nm           # Symbol extractor
tiarm-objdump      # Object dump
tiarm-size         # Size information
```

**Usage in Bin-Xray:**
```
SDK Tools: /opt/ti/ti-cgt-armllvm_2.1.0.LTS/bin/
```

**TI C6000 Code Generation Tools** (C6x DSP)

```bash
# For C6000 DSP
SDK_TOOLS=/opt/ti/ti-cgt-c6000_X.X.X/bin/

# Tools:
cl6x               # Compiler
ar6x               # Archiver  
nm6x               # Name utility
```

### ARM GNU Toolchain

**ARM Embedded GCC**

```bash
# Download from: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain

# Installation
wget https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2
tar xjf gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2
sudo mv gcc-arm-none-eabi-10.3-2021.10 /opt/

# Tools location
SDK_TOOLS=/opt/gcc-arm-none-eabi-10.3-2021.10/bin/

# Available tools:
arm-none-eabi-readelf
arm-none-eabi-nm
arm-none-eabi-objdump
arm-none-eabi-objcopy
arm-none-eabi-size
arm-none-eabi-ar
```

**ARM AArch64 (64-bit)**

```bash
# Ubuntu package
sudo apt-get install gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu

# Tools:
aarch64-linux-gnu-readelf
aarch64-linux-gnu-nm
aarch64-linux-gnu-objdump
```

### NXP

**S32 Design Studio for ARM**

```bash
# Download from: https://www.nxp.com/design/software/development-software/s32-design-studio-ide

# Typical installation
SDK_TOOLS=/opt/NXP/S32DS_ARM_v2.2/S32DS/build_tools/gcc-6.3-arm32-eabi/bin/

# Tools (same as ARM GNU):
arm-none-eabi-readelf
arm-none-eabi-nm
# etc.
```

### Qualcomm

**Hexagon SDK**

```bash
# Download from Qualcomm Developer Network
# Installation path varies

SDK_TOOLS=/opt/qualcomm/hexagon/tools/HEXAGON_Tools/8.x/Tools/bin/

# Tools:
hexagon-readelf
hexagon-nm
hexagon-objdump
hexagon-size
```

**SNPE (Snapdragon Neural Processing Engine)**

```bash
SDK_TOOLS=/opt/qualcomm/snpe/X.X.X/bin/

# Additional SNPE tools:
snpe-dlc-info      # DLC model info
snpe-dlc-viewer    # Model viewer
```

### Renesas

**RX Family Toolchain**

```bash
SDK_TOOLS=/opt/Renesas/e2studio/DebugComp/RX/rx-elf-gcc/bin/

# Tools:
rx-elf-readelf
rx-elf-nm
rx-elf-objdump
```

### RISC-V

**RISC-V GNU Toolchain**

```bash
# Build from source or use prebuilt
# https://github.com/riscv-collab/riscv-gnu-toolchain

SDK_TOOLS=/opt/riscv/bin/

# Tools:
riscv64-unknown-elf-readelf
riscv64-unknown-elf-nm
riscv64-unknown-elf-objdump
```

### Infineon / Cypress

**ModusToolbox**

```bash
SDK_TOOLS=/opt/ModusToolbox/tools_X.X/gcc/bin/

# Tools (ARM-based):
arm-none-eabi-readelf
# etc.
```

### Microchip

**XC32 Compiler (PIC32, SAM)**

```bash
# Windows: C:\Program Files\Microchip\xc32\vX.XX\bin\
# Linux: /opt/microchip/xc32/vX.XX/bin/

SDK_TOOLS=/opt/microchip/xc32/v4.21/bin/

# Tools:
xc32-readelf
xc32-nm
xc32-objdump
xc32-bin2hex
```

## Tool Detection Logic

Bin-Xray automatically detects SDK-specific tools using this priority:

1. **SDK Tools Path**: If you specify a path, it searches for:
   - Exact tool name (e.g., `readelf`)
   - Prefixed versions (e.g., `arm-none-eabi-readelf`, `tiarm-readelf`)

2. **System PATH**: Falls back to system-installed tools

3. **Common Prefixes Tried** (in order):
   ```
   arm-none-eabi-
   tiarm-
   aarch64-linux-gnu-
   arm-linux-gnueabihf-
   riscv64-unknown-elf-
   hexagon-
   rx-elf-
   (no prefix)
   ```

## Verifying Tool Installation

### Quick Check Script

```bash
#!/bin/bash
# verify_tools.sh

echo "Checking required tools..."

TOOLS=("readelf" "nm" "objdump" "ar" "file")

for tool in "${TOOLS[@]}"; do
    if command -v $tool &> /dev/null; then
        version=$($tool --version 2>&1 | head -n1)
        echo "✓ $tool: $version"
    else
        echo "✗ $tool: NOT FOUND"
    fi
done

echo ""
echo "Checking SDK toolchains..."

# TI ARM
if [ -d "/opt/ti" ]; then
    echo "Found TI toolchains in /opt/ti"
    find /opt/ti -name "*readelf" -o -name "*nm" 2>/dev/null | head -5
fi

# ARM GNU
if command -v arm-none-eabi-gcc &> /dev/null; then
    echo "✓ ARM GNU toolchain detected"
    arm-none-eabi-gcc --version | head -1
fi
```

### Python Verification

```python
#!/usr/bin/env python3
import subprocess
import sys

def check_tool(tool_name):
    """Check if a tool is available."""
    try:
        result = subprocess.run(['which', tool_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = subprocess.run([tool_name, '--version'],
                                   capture_output=True, text=True)
            print(f"✓ {tool_name}: {version.stdout.splitlines()[0]}")
            return True
        else:
            print(f"✗ {tool_name}: NOT FOUND")
            return False
    except Exception as e:
        print(f"✗ {tool_name}: ERROR - {e}")
        return False

# Check required tools
tools = ['readelf', 'nm', 'objdump', 'ar', 'file']
results = [check_tool(tool) for tool in tools]

if all(results):
    print("\n✓ All required tools are available!")
    sys.exit(0)
else:
    print("\n✗ Some tools are missing. Please install binutils.")
    sys.exit(1)
```

## Troubleshooting

### "Tool not found" error

**Problem**: Bin-Xray can't find required tools

**Solutions**:
1. Install binutils: `sudo apt-get install binutils`
2. Add tools to PATH: `export PATH=/path/to/sdk/bin:$PATH`

### Wrong architecture detected

**Problem**: Tool outputs garbage or errors

**Solutions**:
1. Ensure you're using the correct toolchain for your binary
2. Specify SDK Tools path for cross-compiled binaries
3. TI binaries need TI tools, ARM needs ARM tools, etc.

### Permission denied

**Problem**: Can't execute tools

**Solutions**:
```bash
# Make tools executable
chmod +x /path/to/sdk/bin/*

# Check ownership
ls -la /path/to/sdk/bin/
```

### Tool timeout

**Problem**: Analysis takes too long

**Solutions**:
1. Reduce binary size (strip debug symbols)
2. Increase timeout in code (default: 30s)
3. Use faster storage (SSD vs HDD)

## Custom Tool Configuration

### Configuring Non-Standard Tools

Edit `src/bin_xray.py` to add custom tool detection:

```python
def _detect_tools(self):
    # ... existing code ...
    
    # Add custom toolchain
    if 'my_custom_sdk' in self.sdk_tools_path.lower():
        custom_prefix = 'myprefix-'
        for tool in ['readelf', 'nm', 'objdump']:
            tool_path = os.path.join(self.sdk_tools_path, 
                                    f"{custom_prefix}{tool}")
            if os.path.exists(tool_path):
                self.tools[tool] = tool_path
```

### Using Alternative Tools

If standard tools aren't available, configure alternatives:

```python
# Use llvm-readelf instead of readelf
if not self.tools.get('readelf'):
    llvm_readelf = subprocess.run(['which', 'llvm-readelf'],
                                 capture_output=True, text=True)
    if llvm_readelf.returncode == 0:
        self.tools['readelf'] = llvm_readelf.stdout.strip()
```

## Performance Notes

### Tool Speed Comparison

| Tool | Speed | Memory Usage | Best For |
|------|-------|--------------|----------|
| readelf | Fast | Low | ELF analysis |
| nm | Very Fast | Very Low | Symbol extraction |
| objdump | Medium | Medium | Disassembly |
| ldd | Fast | Low | Runtime deps |

### Optimization Tips

1. **Use nm over readelf -s** for symbol extraction (faster)
2. **Cache tool paths** to avoid repeated `which` calls
3. **Run tools in parallel** for multiple files
4. **Use --defined-only** flag to reduce nm output

## References

- [GNU Binutils Documentation](https://sourceware.org/binutils/docs/)
- [ELF Format Specification](https://refspecs.linuxfoundation.org/elf/elf.pdf)
- [ARM GNU Toolchain](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain)
- [TI Code Generation Tools](https://www.ti.com/tool/ARM-CGT)
- [RISC-V Toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain)
