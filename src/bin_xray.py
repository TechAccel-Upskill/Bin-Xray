#!/usr/bin/env python3
"""
Bin-Xray: Binary Dependency Analyzer for Embedded Systems

A GUI tool for visualizing dependency relationships in SDK build outputs,
particularly for automotive/ADAS SDKs (TI Jacinto, NXP, Qualcomm, etc.).

Author: Generated for embedded systems development
License: MIT
"""

import os
import re
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
import json
import platform

import networkx as nx

# Import tkinter only if available (needed for GUI, not for core functionality)
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None
    ttk = None
    filedialog = None
    messagebox = None
    scrolledtext = None

# Import modern UI components
try:
    from ui import ModernMainWindow
    USE_MODERN_UI = True
except ImportError:
    try:
        from .ui import ModernMainWindow
        USE_MODERN_UI = True
    except ImportError:
        USE_MODERN_UI = False
        print("Note: Using legacy UI (modern UI components not available)")


# ==============================================================================
# Helper Functions
# ==============================================================================

def is_linker_artifact(name: str) -> bool:
    """Check if a name is a linker script artifact, not a real file."""
    if not name:
        return True

    token = name.strip().rstrip(',;')
    
    # Linker script wildcards and patterns
    if token.startswith('*'):  # *(.text), *(.data), etc.
        return True
    if token in ['*', '*(', '*)', '.']:  # Pure wildcards
        return True
    if token.startswith('PROVIDE'):  # PROVIDE symbols
        return True
    if token.startswith('HIDDEN'):  # HIDDEN symbols
        return True
    if token.startswith('EXCLUDE_FILE('):  # EXCLUDE_FILE(*crtend?.o)
        return True
    if re.match(r'^\*\(\.[\w.]+\)$', token):  # *(.section)
        return True
    if re.search(r'[\*\?][^\s]*\.o(?:bj)?\)?$', token):  # *crtend?.o / wildcard object specs
        return True
    
    # Linker-generated symbols
    linker_symbols = [
        '__bss_start', '__bss_end', '__data_start', '__data_end',
        '_edata', '_end', '_etext', '__stack', '__heap',
        '__init_array_start', '__init_array_end',
        '__fini_array_start', '__fini_array_end'
    ]
    if token in linker_symbols:
        return True
    
    return False


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class Symbol:
    """Represents a symbol in a binary or library."""
    name: str
    type: str  # 'T' (text), 'D' (data), 'U' (undefined), etc.
    size: int = 0
    address: int = 0
    source: str = ""  # Object file or library that defines this


@dataclass
class BinaryInfo:
    """Information extracted from a binary file."""
    path: str
    name: str
    format: str = ""  # ELF, PE, etc.
    architecture: str = ""
    dynamic_deps: List[str] = field(default_factory=list)
    defined_symbols: List[Symbol] = field(default_factory=list)
    undefined_symbols: List[Symbol] = field(default_factory=list)
    sections: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class MapFileInfo:
    """Information extracted from a linker map file."""
    path: str
    memory_regions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    section_map: Dict[str, List[str]] = field(default_factory=dict)  # section -> [objects]
    symbol_xref: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)  # symbol -> {defined_by, used_by}
    unresolved: List[str] = field(default_factory=list)


# ==============================================================================
# Binary Parser - Handles ELF/executable analysis
# ==============================================================================

class BinaryParser:
    """Parse binary files (.elf, .out, .axf, .bin) to extract dependencies and symbols."""
    
    def __init__(self, sdk_tools_path: Optional[str] = None):
        """
        Initialize parser with optional SDK-specific tools.
        
        Args:
            sdk_tools_path: Directory containing SDK-specific tools (readelf, nm, etc.)
        """
        self.sdk_tools_path = sdk_tools_path
        self.tool_prefix = ""  # e.g., "arm-none-eabi-", "tiarm-"
        self._detect_tools()
    
    def _detect_tools(self):
        """Detect available binary analysis tools."""
        self.tools = {}
        tool_names = ['readelf', 'nm', 'objdump', 'ldd', 'file']
        
        # Check for prefixed versions if SDK path provided
        if self.sdk_tools_path:
            # Try common embedded toolchain prefixes
            prefixes = ['arm-none-eabi-', 'tiarm-', 'aarch64-linux-gnu-', 
                       'arm-linux-gnueabihf-', 'riscv64-unknown-elf-', '']
            
            for prefix in prefixes:
                for tool in tool_names:
                    tool_path = os.path.join(self.sdk_tools_path, f"{prefix}{tool}")
                    if os.path.isfile(tool_path) and os.access(tool_path, os.X_OK):
                        self.tools[tool] = tool_path
                        if prefix and not self.tool_prefix:
                            self.tool_prefix = prefix
                if self.tools:  # Found tools with this prefix
                    break
        
        # Fall back to system tools
        for tool in tool_names:
            if tool not in self.tools:
                try:
                    result = subprocess.run(['which', tool], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.tools[tool] = result.stdout.strip()
                except Exception:
                    pass
    
    def _run_tool(self, tool: str, args: List[str]) -> Tuple[bool, str, str]:
        """
        Run a binary analysis tool.
        
        Returns:
            (success, stdout, stderr)
        """
        if tool not in self.tools:
            return False, "", f"Tool '{tool}' not found"
        
        try:
            cmd = [self.tools[tool]] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Tool execution timed out"
        except Exception as e:
            return False, "", str(e)
    
    def parse_binary(self, binary_path: str) -> BinaryInfo:
        """
        Parse a binary file and extract all relevant information.
        
        Args:
            binary_path: Path to the binary file
            
        Returns:
            BinaryInfo object with extracted data
        """
        info = BinaryInfo(path=binary_path, name=os.path.basename(binary_path))
        
        # Detect file format
        success, stdout, _ = self._run_tool('file', [binary_path])
        if success:
            info.format = self._parse_file_type(stdout)
            info.architecture = self._parse_architecture(stdout)
        
        # Extract dynamic dependencies (for ELF)
        if 'ELF' in info.format:
            info.dynamic_deps = self._parse_dynamic_deps(binary_path)
        
        # Extract symbols
        info.defined_symbols, info.undefined_symbols = self._parse_symbols(binary_path)
        
        # Extract section information
        info.sections = self._parse_sections(binary_path)
        
        return info
    
    def _parse_file_type(self, file_output: str) -> str:
        """Extract file type from 'file' command output."""
        if 'ELF' in file_output:
            return 'ELF'
        elif 'PE32' in file_output or 'MS-DOS' in file_output:
            return 'PE'
        elif 'Mach-O' in file_output:
            return 'Mach-O'
        else:
            return 'Unknown'
    
    def _parse_architecture(self, file_output: str) -> str:
        """Extract architecture from 'file' command output."""
        arch_patterns = {
            r'ARM|arm': 'ARM',
            r'aarch64|ARM64': 'ARM64',
            r'x86-64|x86_64': 'x86_64',
            r'i386|80386': 'i386',
            r'MIPS': 'MIPS',
            r'RISC-V|riscv': 'RISC-V',
        }
        
        for pattern, arch in arch_patterns.items():
            if re.search(pattern, file_output, re.IGNORECASE):
                return arch
        
        return 'Unknown'
    
    def _parse_dynamic_deps(self, binary_path: str) -> List[str]:
        """Extract dynamic library dependencies using readelf."""
        deps = []
        success, stdout, _ = self._run_tool('readelf', ['-d', binary_path])
        
        if success:
            # Look for NEEDED entries
            for line in stdout.splitlines():
                match = re.search(r'NEEDED.*\[(.*?)\]', line)
                if match:
                    deps.append(match.group(1))
        
        return deps
    
    def _parse_symbols(self, binary_path: str) -> Tuple[List[Symbol], List[Symbol]]:
        """
        Extract symbols using nm.
        
        Returns:
            (defined_symbols, undefined_symbols)
        """
        defined = []
        undefined = []
        
        success, stdout, _ = self._run_tool('nm', ['-C', '--print-size', binary_path])
        
        if success:
            for line in stdout.splitlines():
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                # Parse nm output format
                # Undefined:        U symbol_name
                # Defined:   address [size] type symbol_name
                sym = Symbol(name="", type="")
                
                if parts[0] == 'U':  # Undefined symbol (no address)
                    sym.type = 'U'
                    sym.name = ' '.join(parts[1:])
                    undefined.append(sym)
                else:
                    try:
                        sym.address = int(parts[0], 16)
                        if len(parts) >= 4:  # Has size
                            sym.size = int(parts[1], 16)
                            sym.type = parts[2]
                            sym.name = ' '.join(parts[3:])
                        else:
                            sym.type = parts[1]
                            sym.name = ' '.join(parts[2:])
                        
                        # Only add defined symbols (T, D, R, B, etc.)
                        if sym.type in 'TtDdRrBbVv':
                            defined.append(sym)
                    except (ValueError, IndexError):
                        continue
        
        return defined, undefined
    
    def _parse_sections(self, binary_path: str) -> Dict[str, Dict[str, Any]]:
        """Extract section information using readelf."""
        sections = {}
        success, stdout, _ = self._run_tool('readelf', ['-S', binary_path])
        
        if success:
            # Parse section headers
            for line in stdout.splitlines():
                # Look for section entries: [ 1] .text PROGBITS ...
                match = re.match(r'\s*\[\s*\d+\]\s+(\S+)\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', line)
                if match:
                    name, sec_type, address, offset, size = match.groups()
                    sections[name] = {
                        'type': sec_type,
                        'address': int(address, 16),
                        'offset': int(offset, 16),
                        'size': int(size, 16)
                    }
        
        return sections


# ==============================================================================
# Map File Parser - Handles linker map file analysis
# ==============================================================================

class MapFileParser:
    """Parse linker map files to extract symbol cross-references and memory layout."""
    
    def __init__(self):
        self.supported_formats = ['GNU ld', 'TI linker', 'ARM linker', 'IAR linker']
    
    def parse_map_file(self, map_path: str) -> MapFileInfo:
        """
        Parse a linker map file.
        
        Args:
            map_path: Path to the .map file
            
        Returns:
            MapFileInfo object with extracted data
        """
        info = MapFileInfo(path=map_path)
        
        try:
            with open(map_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect map file format
            map_format = self._detect_format(content)
            
            # Parse based on format
            if 'GNU' in map_format or 'ld' in map_format.lower():
                self._parse_gnu_map(content, info)
            elif 'TI' in map_format:
                self._parse_ti_map(content, info)
            else:
                # Try generic parsing
                self._parse_generic_map(content, info)
        
        except Exception as e:
            print(f"Error parsing map file: {e}")
        
        return info
    
    def _detect_format(self, content: str) -> str:
        """Detect the linker map file format."""
        first_lines = '\n'.join(content.splitlines()[:50])
        
        if 'GNU ld' in first_lines or 'Memory Configuration' in first_lines:
            return 'GNU ld'
        elif 'TMS320' in first_lines or 'Texas Instruments' in first_lines:
            return 'TI linker'
        elif 'ARM Linker' in first_lines or 'armlink' in first_lines:
            return 'ARM linker'
        elif 'IAR' in first_lines:
            return 'IAR linker'
        
        return 'Unknown'
    
    def _parse_gnu_map(self, content: str, info: MapFileInfo):
        """Parse GNU ld map file format."""
        lines = content.splitlines()
        
        # Parse memory regions
        in_memory_config = False
        in_cross_ref = False
        
        for i, line in enumerate(lines):
            # Memory Configuration section
            if 'Memory Configuration' in line:
                in_memory_config = True
                continue
            elif in_memory_config and (line.strip() == '' or line.startswith('Linker')):
                in_memory_config = False
            
            if in_memory_config:
                # Parse: Name             Origin             Length             Attributes
                match = re.match(r'(\S+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)', line, re.IGNORECASE)
                if match:
                    name, origin, length = match.groups()
                    info.memory_regions[name] = {
                        'origin': int(origin, 16),
                        'length': int(length, 16)
                    }
            
            # Cross Reference Table
            if 'Cross Reference Table' in line or 'CROSS REFERENCE TABLE' in line:
                in_cross_ref = True
                continue
            elif in_cross_ref and line.strip() == '':
                # Check if this is the blank line after the header, skip it
                if i + 1 < len(lines) and lines[i + 1].startswith('Symbol'):
                    # Skip header line, continue parsing
                    continue
                else:
                    in_cross_ref = False
            
            # Skip header line
            if in_cross_ref and line.startswith('Symbol') and 'File' in line:
                continue
            
            if in_cross_ref and line.strip():
                # Parse symbol cross references
                self._parse_cross_ref_line(line, info)
            
            # Section mapping: .text sections
            if line.startswith('.text') or line.startswith('.data') or line.startswith('.bss'):
                self._parse_section_line(line, info, lines, i)
        
        # Parse output section information
        self._parse_output_sections(content, info)
    
    def _parse_cross_ref_line(self, line: str, info: MapFileInfo):
        """Parse a line from the cross-reference table."""
        # Format: symbol_name    defined_in.o    used_by1.o used_by2.o ...
        parts = line.split()
        if len(parts) < 2:
            return
        
        symbol = parts[0]
        
        # Filter out linker artifacts
        if is_linker_artifact(symbol):
            return
        
        if symbol not in info.symbol_xref:
            info.symbol_xref[symbol] = {'defined_by': [], 'used_by': []}
        
        # First file is usually the definer
        for part in parts[1:]:
            # Filter out linker artifacts in file names
            if is_linker_artifact(part):
                continue
            if part.endswith(('.o', '.a', '.so', '.obj')):
                if not info.symbol_xref[symbol]['defined_by']:
                    info.symbol_xref[symbol]['defined_by'].append(part)
                else:
                    info.symbol_xref[symbol]['used_by'].append(part)
    
    def _parse_section_line(self, line: str, info: MapFileInfo, all_lines: List[str], idx: int):
        """Parse section placement information."""
        match = re.match(r'(\.[\w.]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)', line, re.IGNORECASE)
        if match:
            section, address, size = match.groups()
            
            # Look ahead for object files contributing to this section
            objects = []
            for j in range(idx + 1, min(idx + 20, len(all_lines))):
                next_line = all_lines[j]
                if next_line.strip() == '' or next_line.startswith('.'):
                    break
                # Extract object file names
                obj_match = re.search(r'(\S+\.o(?:bj)?)', next_line)
                if obj_match:
                    obj_name = obj_match.group(1)
                    # Filter out linker artifacts
                    if not is_linker_artifact(obj_name):
                        objects.append(obj_name)
            
            if section not in info.section_map:
                info.section_map[section] = []
            info.section_map[section].extend(objects)
    
    def _parse_output_sections(self, content: str, info: MapFileInfo):
        """Parse output section details for memory usage."""
        # Look for patterns like:
        # .text           0x00000000    0x12345
        #  .text.startup  0x00000000    0x100    object.o
        pattern = r'^\s*(\.[\w.]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)(?:\s+(\S+))?'
        
        for line in content.splitlines():
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                section, addr, size, source = match.groups()
                if source and source.endswith(('.o', '.obj', '.a')):
                    if is_linker_artifact(source):
                        continue
                    if section not in info.section_map:
                        info.section_map[section] = []
                    if source not in info.section_map[section]:
                        info.section_map[section].append(source)
    
    def _parse_ti_map(self, content: str, info: MapFileInfo):
        """Parse TI-specific map file format (TMS320, Jacinto SDK)."""
        # TI map files have different sections
        lines = content.splitlines()
        
        in_output_section = False
        
        for line in lines:
            # TI memory configuration: MEMORY { ... }
            if 'OUTPUT SECTION' in line.upper():
                in_output_section = True
                continue
            
            # Parse TI-specific cross-reference format
            if 'GLOBAL SYMBOLS' in line.upper():
                in_output_section = False
                # Parse symbol table
                continue
            
            if in_output_section:
                # Parse: .text    0x00000000   0x12345  filename.obj
                match = re.match(r'\s*(\.[\w.]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+(\S+)', line, re.IGNORECASE)
                if match:
                    section, addr, size, obj_file = match.groups()
                    if is_linker_artifact(obj_file):
                        continue
                    if section not in info.section_map:
                        info.section_map[section] = []
                    info.section_map[section].append(obj_file)
    
    def _parse_generic_map(self, content: str, info: MapFileInfo):
        """Generic map file parser for unknown formats."""
        # Try to extract any useful information
        lines = content.splitlines()
        
        for line in lines:
            # Look for common patterns
            # Section: address size
            match = re.match(r'\s*(\.[\w.]+|[A-Z_]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)', line, re.IGNORECASE)
            if match:
                section, addr, size = match.groups()
                if section not in info.section_map:
                    info.section_map[section] = []
            
            # Object files
            obj_match = re.search(r'(\S+\.o(?:bj)?|\S+\.a)', line)
            if obj_match:
                obj_file = obj_match.group(1)
                if is_linker_artifact(obj_file):
                    continue
                # Associate with the last seen section
                if info.section_map:
                    last_section = list(info.section_map.keys())[-1]
                    if obj_file not in info.section_map[last_section]:
                        info.section_map[last_section].append(obj_file)


# ==============================================================================
# Library Parser - Handles .a / .so analysis
# ==============================================================================

class LibraryParser:
    """Parse static (.a) and shared (.so, .dll) libraries."""
    
    def __init__(self, sdk_tools_path: Optional[str] = None):
        self.sdk_tools_path = sdk_tools_path
        self.binary_parser = BinaryParser(sdk_tools_path)
    
    def parse_library(self, lib_path: str) -> Dict[str, List[Symbol]]:
        """
        Parse a library file and extract symbols.
        
        Args:
            lib_path: Path to the library file
            
        Returns:
            Dictionary mapping object file names to their symbols
        """
        lib_symbols = {}
        
        if lib_path.endswith('.a'):
            lib_symbols = self._parse_static_library(lib_path)
        elif lib_path.endswith(('.so', '.dll', '.dylib')):
            lib_symbols = self._parse_shared_library(lib_path)
        elif lib_path.endswith('.o') or '/tmp/' in lib_path:  # Handle object files
            lib_symbols = self._parse_object_file(lib_path)
        
        return lib_symbols
    
    def _parse_static_library(self, lib_path: str) -> Dict[str, List[Symbol]]:
        """Parse static archive (.a) file."""
        symbols_by_object = {}
        
        # Use 'ar -t' to list archive members
        tool = 'ar'
        try:
            result = subprocess.run([tool, '-t', lib_path], capture_output=True, text=True)
            if result.returncode == 0:
                object_files = result.stdout.splitlines()
                
                # Extract symbols from each object file
                for obj in object_files:
                    obj = obj.strip()
                    if not obj:
                        continue

                    # Always register archive members as objects, even if symbol
                    # extraction fails on this environment/toolchain.
                    symbols_by_object.setdefault(obj, [])

                    success, stdout, _ = self.binary_parser._run_tool('nm', ['-C', lib_path, obj])
                    if success:
                        symbols = []
                        for line in stdout.splitlines():
                            parts = line.split()
                            if len(parts) >= 2:
                                sym = Symbol(name=' '.join(parts[2:]) if len(parts) > 2 else parts[1],
                                           type=parts[1] if len(parts) > 2 else 'U')
                                symbols.append(sym)
                        
                        symbols_by_object[obj] = symbols
        except Exception as e:
            print(f"Error parsing static library {lib_path}: {e}")
        
        return symbols_by_object
    
    def _parse_shared_library(self, lib_path: str) -> Dict[str, List[Symbol]]:
        """Parse shared library (.so, .dll) file."""
        symbols = {}
        
        # Treat as a binary
        binary_info = self.binary_parser.parse_binary(lib_path)
        
        # Store all symbols under the library name
        lib_name = os.path.basename(lib_path)
        all_symbols = binary_info.defined_symbols + binary_info.undefined_symbols
        symbols[lib_name] = all_symbols
        
        return symbols
    
    def _parse_object_file(self, obj_path: str) -> Dict[str, List[Symbol]]:
        """Parse object file (.o) file."""
        symbols = {}
        
        # Parse as a binary
        binary_info = self.binary_parser.parse_binary(obj_path)
        
        # Store under object file name
        obj_name = os.path.basename(obj_path)
        all_symbols = binary_info.defined_symbols + binary_info.undefined_symbols
        symbols[obj_name] = all_symbols
        
        return symbols


# ==============================================================================
# Dependency Graph Builder
# ==============================================================================

class DependencyGraphBuilder:
    """Build a dependency graph from parsed binary, map, and library information."""
    
    def __init__(self, max_depth: int = 6):
        self.graph = nx.MultiDiGraph()
        self.max_depth = max_depth
        self.node_types = {}  # node -> type (binary, library, object, symbol)
        self.node_details = {}  # node -> detailed info
        self.unused_objects = set()  # Track unused object files
        self.unused_libraries = set()  # Track unused libraries
    
    def build_graph(self, 
                   binary_info: Optional[BinaryInfo] = None,
                   map_info: Optional[MapFileInfo] = None,
                   libraries: Optional[Dict[str, Dict[str, List[Symbol]]]] = None,
                   show_symbols: bool = True) -> nx.MultiDiGraph:
        """
        Build the complete dependency graph.
        
        Args:
            binary_info: Parsed binary information
            map_info: Parsed map file information
            libraries: Dictionary of library name -> {object -> symbols}
            show_symbols: If True, add symbol-level dependencies
            
        Returns:
            NetworkX MultiDiGraph
        """
        # Add binary as root node
        if binary_info:
            self._add_binary_node(binary_info)
        
        # Add map file relationships
        if map_info:
            self._add_map_relationships(map_info, show_symbols)
        
        # Add library nodes and detect unused ones
        if libraries:
            self._add_library_nodes(libraries, binary_info, show_symbols)
            self._detect_unused_nodes(binary_info, libraries, map_info)
        
        return self.graph
    
    def _add_binary_node(self, binary_info: BinaryInfo):
        """Add the main binary as a node."""
        node_name = binary_info.name
        self.graph.add_node(node_name)
        self.node_types[node_name] = 'binary'
        self.node_details[node_name] = {
            'path': binary_info.path,
            'format': binary_info.format,
            'architecture': binary_info.architecture,
            'num_symbols': len(binary_info.defined_symbols),
            'num_undefined': len(binary_info.undefined_symbols)
        }
        
        # Add dynamic dependencies
        for dep in binary_info.dynamic_deps:
            self.graph.add_node(dep)
            self.node_types[dep] = 'shared_lib'
            self.graph.add_edge(node_name, dep, label='DT_NEEDED', type='dynamic')
    
    def _add_map_relationships(self, map_info: MapFileInfo, show_symbols: bool = True):
        """Add relationships from map file analysis."""
        # Add object files and their section contributions
        for section, objects in map_info.section_map.items():
            for obj in objects:
                if obj not in self.graph:
                    self.graph.add_node(obj)
                    self.node_types[obj] = 'object'
        
        # Add symbol cross-references with enhanced detail
        if show_symbols:
            for symbol, refs in map_info.symbol_xref.items():
                definers = refs.get('defined_by', [])
                users = refs.get('used_by', [])
                
                # Skip if no cross-references
                if not definers or not users:
                    continue
                
                for definer in definers:
                    if definer not in self.graph:
                        self.graph.add_node(definer)
                        self.node_types[definer] = 'object'
                    
                    for user in users:
                        if user not in self.graph:
                            self.graph.add_node(user)
                            self.node_types[user] = 'object'
                        
                        # Add edge: user -> definer (user depends on definer's symbol)
                        symbol_label = symbol[:30] if len(symbol) <= 30 else symbol[:27] + "..."
                        self.graph.add_edge(user, definer, 
                                          label=symbol_label,
                                          type='symbol_ref',
                                          symbol=symbol)
        else:
            # Just add basic object relationships without symbol details
            for symbol, refs in map_info.symbol_xref.items():
                definers = refs.get('defined_by', [])
                users = refs.get('used_by', [])
                
                for definer in definers:
                    if definer not in self.graph:
                        self.graph.add_node(definer)
                        self.node_types[definer] = 'object'
                    
                    for user in users:
                        if user not in self.graph:
                            self.graph.add_node(user)
                            self.node_types[user] = 'object'
                        
                        # Add edge without symbol label (simpler)
                        if not self.graph.has_edge(user, definer):
                            self.graph.add_edge(user, definer, type='depends_on')
    
    def _add_library_nodes(self, libraries: Dict[str, Dict[str, List[Symbol]]], 
                          binary_info: Optional[BinaryInfo],
                          show_symbols: bool = True):
        """Add library nodes and their relationships."""
        # First pass: collect all object files and their symbols
        all_objects = {}  # obj_name -> (lib_path, symbols)
        
        for lib_path, objects in libraries.items():
            lib_name = os.path.basename(lib_path)
            
            if lib_name not in self.graph:
                self.graph.add_node(lib_name)
            
            # Determine library type
            if lib_path.endswith('.a'):
                self.node_types[lib_name] = 'static_lib'
            elif lib_path.endswith('.o'):
                self.node_types[lib_name] = 'object'
            else:
                self.node_types[lib_name] = 'shared_lib'
            
            self.node_details[lib_name] = {'path': lib_path, 'num_objects': len(objects)}
            
            # Add constituent object files
            for obj_name, symbols in objects.items():
                # For .o files directly added, use lib_name; for .a archives, use full_obj_name
                if lib_path.endswith('.o'):
                    node_name = lib_name
                else:
                    node_name = f"{lib_name}:{obj_name}"
                
                if node_name not in self.graph:
                    self.graph.add_node(node_name)
                    self.node_types[node_name] = 'object'
                    self.node_details[node_name] = {'num_symbols': len(symbols)}
                
                # Link library to object (only for archives)
                if not lib_path.endswith('.o'):
                    self.graph.add_edge(lib_name, node_name, type='contains')
                
                # Store for symbol matching
                all_objects[node_name] = (lib_path, symbols)
        
        # Second pass: match undefined symbols with defined symbols
        if show_symbols:
            for obj_name, (obj_path, obj_symbols) in all_objects.items():
                # Get undefined symbols from this object
                undefined = [s for s in obj_symbols if s.type == 'U']
                
                # Match with defined symbols from other objects
                for undef_sym in undefined:
                    for other_obj_name, (other_path, other_symbols) in all_objects.items():
                        if obj_name == other_obj_name:
                            continue
                        
                        # Check if other object defines this symbol
                        for def_sym in other_symbols:
                            if def_sym.name == undef_sym.name and def_sym.type in 'TtDdRrBbVv':
                                # obj_name needs undef_sym from other_obj_name
                                self.graph.add_edge(obj_name, other_obj_name,
                                                  label=undef_sym.name[:30],
                                                  type='symbol_ref',
                                                  symbol=undef_sym.name)
                                break
            
            # Also check binary's undefined symbols against library symbols
            if binary_info:
                for bin_undef in binary_info.undefined_symbols:
                    for obj_name, (obj_path, obj_symbols) in all_objects.items():
                        for lib_sym in obj_symbols:
                            if lib_sym.name == bin_undef.name and lib_sym.type in 'TtDdRrBbVv':
                                # Binary needs this symbol from library object
                                self.graph.add_edge(binary_info.name, obj_name,
                                                  label=bin_undef.name[:30],
                                                  type='symbol_ref',
                                                  symbol=bin_undef.name)
                                break
    
    def _detect_unused_nodes(self, binary_info, _libraries, map_info: Optional[MapFileInfo] = None):
        """Detect unused objects and libraries."""
        # Step 1: Build library -> objects mapping
        library_objects = {}
        for node in self.graph.nodes():
            node_type = self.node_types.get(node, '')
            if node_type in ['library', 'static_lib', 'shared_lib']:
                # Find objects contained in this library
                library_objects[node] = []
                for u, v, data in self.graph.edges(data=True):
                    if u == node and data.get('type') == 'contains' and self.node_types.get(v) == 'object':
                        library_objects[node].append(v)
        
        # Step 2: Determine used libraries (libraries that binary depends on)
        used_libraries = set()
        if binary_info:
            for lib_node in library_objects.keys():
                # Check dynamic dependencies
                if self.graph.has_edge(binary_info.name, lib_node):
                    for u, v, data in self.graph.edges(data=True):
                        if u == binary_info.name and v == lib_node and data.get('type') in ['dynamic', 'depends_on']:
                            used_libraries.add(lib_node)
                            break

        # Step 2b: Fallback library usage from map entries.
        # Some environments parse fewer archive members (e.g., tool differences),
        # but map section placement still reveals which libraries contributed.
        map_used_libraries = set()
        if map_info:
            for section_objects in map_info.section_map.values():
                for item in section_objects:
                    token = str(item).strip()
                    if not token:
                        continue

                    # Match patterns like "libfoo.a(bar.o)" or "libfoo.a:bar.o"
                    match = re.match(r'([^\s:()]+\.(?:a|so|dll|dylib))\s*(?:\(|:)', token)
                    if match:
                        map_used_libraries.add(os.path.basename(match.group(1)))
                        continue

                    # If the entry itself is a library path/name, count it as used.
                    base = os.path.basename(token)
                    if base.endswith(('.a', '.so', '.dll', '.dylib')):
                        map_used_libraries.add(base)

        if map_used_libraries:
            for lib_node in library_objects.keys():
                if os.path.basename(lib_node) in map_used_libraries:
                    used_libraries.add(lib_node)
        
        # Step 3: Mark objects as used if:
        # - They are in a used library, OR
        # - They have symbol dependencies (symbol_ref edges), OR
        # - They are directly referenced by binary, OR
        # - They appear in map section placement (fallback when symbol tools differ across envs)
        used_objects = set()

        # Build a normalized set of object names seen in the map file.
        # This provides a stable fallback signal on platforms where symbol extraction differs.
        map_objects = set()
        if map_info:
            for section_objects in map_info.section_map.values():
                for obj in section_objects:
                    if not obj:
                        continue
                    map_objects.add(str(obj).strip())
                    map_objects.add(os.path.basename(str(obj).strip()))

        def _node_matches_map_object(node_name: str) -> bool:
            # Supports formats like "libfoo.a:bar.o", "libfoo.a(bar.o)", and plain "bar.o"
            candidates = {node_name, os.path.basename(node_name)}
            if ':' in node_name:
                _, rhs = node_name.split(':', 1)
                candidates.add(rhs.strip())
                candidates.add(os.path.basename(rhs.strip()))
            if '(' in node_name and node_name.endswith(')'):
                try:
                    rhs = node_name.rsplit('(', 1)[1].rstrip(')').strip()
                    candidates.add(rhs)
                    candidates.add(os.path.basename(rhs))
                except Exception:
                    pass
            return any(item in map_objects for item in candidates if item)
        
        for node in self.graph.nodes():
            node_type = self.node_types.get(node, '')
            if node_type == 'object':
                is_used = False
                
                # Check if in a used library
                for lib_name, objs in library_objects.items():
                    if node in objs and lib_name in used_libraries:
                        is_used = True
                        break
                
                # Check if has symbol references (used by other objects/binary)
                if not is_used:
                    for u, v, data in self.graph.edges(data=True):
                        if v == node and data.get('type') == 'symbol_ref':
                            is_used = True
                            break
                
                # Check if provides symbols to other objects
                if not is_used:
                    for u, v, data in self.graph.edges(data=True):
                        if u == node and data.get('type') == 'symbol_ref':
                            is_used = True
                            break
                
                # Check if directly referenced by binary
                if not is_used and binary_info:
                    if self.graph.has_edge(binary_info.name, node):
                        is_used = True
                    elif self.graph.has_edge(node, binary_info.name):
                        is_used = True

                # Fallback: object appears in map placement records.
                # This avoids false "all unused" outcomes when symbol tools are missing/limited.
                if not is_used and map_objects:
                    if _node_matches_map_object(node):
                        is_used = True
                
                if is_used:
                    used_objects.add(node)
                else:
                    self.unused_objects.add(node)
        
        # Step 4: Identify unused libraries
        for lib_name in library_objects.keys():
            if lib_name not in used_libraries:
                # Library is not directly used by binary
                # Check if any of its objects are used
                has_used_objects = False
                for obj in library_objects[lib_name]:
                    if obj in used_objects:
                        has_used_objects = True
                        break
                
                if not has_used_objects:
                    self.unused_libraries.add(lib_name)
        
        # Step 5: Mark unused nodes with special attribute
        for node in self.unused_objects | self.unused_libraries:
            if node in self.graph:
                self.graph.nodes[node]['unused'] = True
    
    def get_unused_summary(self):
        """Get summary of unused objects and libraries."""
        return {
            'unused_objects': sorted(list(self.unused_objects)),
            'unused_libraries': sorted(list(self.unused_libraries)),
            'total_unused': len(self.unused_objects) + len(self.unused_libraries)
        }
    
    def get_build_efficiency_score(self):
        """Calculate build efficiency score (0-100).
        
        Score indicates how efficiently the build system is configured:
        - 100 = Perfect: All built components are used
        - 90-99 = Excellent: Very few unused components
        - 70-89 = Good: Some optimization possible
        - 50-69 = Fair: Significant unused components
        - 0-49 = Poor: Many unused components wasting build time
        """
        total_objects = len(self.unused_objects)

        # Libraries for efficiency scoring should represent build inputs
        # (archives/shared libs provided to analysis), not runtime DT_NEEDED deps.
        build_library_nodes = [
            n for n in self.graph.nodes()
            if self.node_types.get(n) in ['library', 'static_lib', 'shared_lib']
            and bool(self.node_details.get(n, {}).get('path'))
        ]
        build_library_set = set(build_library_nodes)
        total_libraries = len([n for n in self.unused_libraries if n in build_library_set])
        
        # Count total built components
        total_built_objects = len([n for n in self.graph.nodes() 
                                   if self.node_types.get(n) == 'object'])
        total_built_libraries = len(build_library_nodes)
        
        if total_built_objects == 0 and total_built_libraries == 0:
            return 100, "N/A", {}
        
        # Calculate usage percentages
        used_objects = total_built_objects - total_objects
        used_libraries = total_built_libraries - total_libraries
        
        obj_usage_pct = (used_objects / total_built_objects * 100) if total_built_objects > 0 else 100
        lib_usage_pct = (used_libraries / total_built_libraries * 100) if total_built_libraries > 0 else 100
        
        # Weighted average (libraries waste more time than objects)
        if total_built_libraries > 0:
            score = (obj_usage_pct * 0.6) + (lib_usage_pct * 0.4)
        else:
            score = obj_usage_pct
        
        # Determine grade
        if score >= 95:
            grade = "A+ (Excellent)"
        elif score >= 90:
            grade = "A (Very Good)"
        elif score >= 80:
            grade = "B (Good)"
        elif score >= 70:
            grade = "C (Fair)"
        elif score >= 60:
            grade = "D (Needs Optimization)"
        else:
            grade = "F (Poor - Wasting Build Time)"
        
        details = {
            'total_built_objects': total_built_objects,
            'used_objects': used_objects,
            'unused_objects': total_objects,
            'object_usage_pct': obj_usage_pct,
            'total_built_libraries': total_built_libraries,
            'used_libraries': used_libraries,
            'unused_libraries': total_libraries,
            'library_usage_pct': lib_usage_pct
        }
        
        return round(score, 1), grade, details
    
    def get_subgraph(self, root_node: str, depth: int = None) -> nx.MultiDiGraph:
        """Get a subgraph starting from a root node up to a certain depth."""
        if depth is None:
            depth = self.max_depth
        
        # BFS to find nodes within depth
        nodes = {root_node}
        current_level = {root_node}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                # Get successors (dependencies)
                next_level.update(self.graph.successors(node))
                # Get predecessors (dependents)
                next_level.update(self.graph.predecessors(node))
            
            nodes.update(next_level)
            current_level = next_level
            
            if not current_level:
                break
        
        return self.graph.subgraph(nodes).copy()


# ==============================================================================
# Main GUI Application
# ==============================================================================

class BinXrayGUI:
    """Main GUI application for Bin-Xray."""
    
    def __init__(self, root):
        self.root = root
        
        # Data storage
        self.binary_info = None
        self.map_info = None
        self.libraries = {}
        self.graph_builder = None
        self.current_graph = None
        
        # Configuration
        self.config_file = os.path.expanduser("~/.binxray_config.json")
        self.config = self._load_config()
        
        # Use modern UI if available
        if USE_MODERN_UI:
            self._init_modern_ui()
        else:
            self._init_legacy_ui()
        
        # Status
        if hasattr(self, 'status_var'):
            self.status_var.set("Ready")
        elif hasattr(self, 'ui'):
            self.ui.set_status("Ready")
    
    def _init_modern_ui(self):
        """Initialize modern UI."""
        callbacks = {
            'analyze': self._analyze_and_generate,
            'copy_report': self._copy_report_modern,
            'export_report': self._export_report_modern,
        }
        
        self.ui = ModernMainWindow(self.root, self.config, callbacks)
        
        # Create references to UI components for compatibility
        self.dependency_text = self.ui.report_text
        self.progress = self.ui.progress
        self.generate_btn = self.ui.generate_btn
        self._configure_report_text_widget()
    
    def _init_legacy_ui(self):
        """Initialize legacy UI."""
        self.root.title("Bin-Xray - Binary Dependency Analyzer")
        self.root.geometry("1400x900")
        self._create_widgets()
        self._create_menu()
    
    def _set_status(self, status_text, color=None):
        """Set status text (works with both modern and legacy UI)."""
        if hasattr(self, 'ui'):
            self.ui.set_status(status_text, color)
        elif hasattr(self, 'status_var'):
            self.status_var.set(status_text)
    
    def _update_stats(self, score=None, libs=None, objs=None):
        """Update statistics (works with modern UI)."""
        if hasattr(self, 'ui'):
            self.ui.update_stats(score=score, libs=libs, objs=objs)
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        default_config = {
            'last_binary': '',
            'last_map': '',
            'last_lib_dir': '',
            'last_sdk_tools': '',
            'graph_depth': 5,
            'layout_algorithm': 'spring',
            'show_symbols': False
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return {**default_config, **json.load(f)}
        except Exception:
            pass
        
        return default_config
    
    def _add_placeholder(self, entry_widget, placeholder_text):
        """Add placeholder text to an entry widget."""
        def on_focus_in(event):
            if entry_widget.get() == placeholder_text:
                entry_widget.delete(0, tk.END)
                entry_widget.config(foreground='black')
        
        def on_focus_out(event):
            if not entry_widget.get():
                entry_widget.insert(0, placeholder_text)
                entry_widget.config(foreground='gray')
        
        # Set initial placeholder if empty
        if not entry_widget.get():
            entry_widget.insert(0, placeholder_text)
            entry_widget.config(foreground='gray')
        
        entry_widget.bind('<FocusIn>', on_focus_in)
        entry_widget.bind('<FocusOut>', on_focus_out)
    
    def _add_tooltip(self, widget, text):
        """Add a tooltip to a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", 
                           relief='solid', borderwidth=1, font=('TkDefaultFont', 9))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def _configure_report_text_widget(self):
        """Make the report text read-only but selectable/copyable."""
        if not hasattr(self, 'dependency_text') or not self.dependency_text:
            return

        self.dependency_text.config(state=tk.NORMAL)
        if getattr(self.dependency_text, '_readonly_configured', False):
            return

        def block_edit(event=None):
            if event is None:
                return 'break'
            # Allow navigation and copy/select shortcuts while blocking edits.
            if event.state & 0x4 and event.keysym.lower() in ('c', 'a'):
                return
            if event.keysym in ('Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next'):
                return
            return 'break'

        self.dependency_text.bind('<Key>', block_edit)
        self.dependency_text.bind('<<Paste>>', block_edit)
        self.dependency_text.bind('<<Cut>>', block_edit)
        self.dependency_text.bind('<Control-x>', block_edit)
        self.dependency_text.bind('<Control-v>', block_edit)
        self.dependency_text.bind('<Control-c>', self._copy_selected_text)
        self.dependency_text.bind('<Control-C>', self._copy_selected_text)
        self.dependency_text.bind('<<Copy>>', self._copy_selected_text)
        self.dependency_text._readonly_configured = True

    def _copy_selected_text(self, event=None):
        """Copy selected text from the report widget to the clipboard."""
        if not hasattr(self, 'dependency_text') or not self.dependency_text:
            return 'break'

        try:
            selection = self.dependency_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return 'break'

        self.root.clipboard_clear()
        self.root.clipboard_append(selection)
        if hasattr(self, 'ui'):
            self.ui.set_status("Selection copied")
            self.root.after(2000, lambda: self.ui.set_status("Ready"))
        return 'break'
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Graph (PNG)", command=lambda: self._export_graph('png'))
        file_menu.add_command(label="Export Graph (SVG)", command=lambda: self._export_graph('svg'))
        file_menu.add_command(label="Export GraphML", command=self._export_graphml)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Reset Zoom", command=self._reset_view)
        view_menu.add_command(label="Show Node Details", command=self._show_node_details)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Required Tools", command=self._show_required_tools)
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # === Input Section ===
        input_frame = ttk.LabelFrame(main_frame, text="Input Files", padding="10")
        input_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(1, weight=1)
        
        # Binary file
        ttk.Label(input_frame, text="Binary:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.binary_var = tk.StringVar(value=self.config.get('last_binary', ''))
        self.binary_entry = ttk.Entry(input_frame, textvariable=self.binary_var)
        self.binary_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self._add_placeholder(self.binary_entry, "e.g., app.elf, firmware.out, binary.axf")
        ttk.Button(input_frame, text="Browse...", command=self._browse_binary).grid(row=0, column=2)
        
        # Map file
        ttk.Label(input_frame, text="Map File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.map_var = tk.StringVar(value=self.config.get('last_map', ''))
        self.map_entry = ttk.Entry(input_frame, textvariable=self.map_var)
        self.map_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self._add_placeholder(self.map_entry, "e.g., output.map, linker.map (optional)")
        ttk.Button(input_frame, text="Browse...", command=self._browse_map).grid(row=1, column=2)
        
        # Library directory
        ttk.Label(input_frame, text="Library Dir:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.libdir_var = tk.StringVar(value=self.config.get('last_lib_dir', ''))
        self.libdir_entry = ttk.Entry(input_frame, textvariable=self.libdir_var)
        self.libdir_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        self._add_placeholder(self.libdir_entry, "e.g., ./libs, ./sdk/lib, ./ (for .o files)")
        ttk.Button(input_frame, text="Browse...", command=self._browse_libdir).grid(row=2, column=2)
        
        # SDK tools path
        ttk.Label(input_frame, text="SDK Tools:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.sdk_tools_var = tk.StringVar(value=self.config.get('last_sdk_tools', ''))
        self.sdk_tools_entry = ttk.Entry(input_frame, textvariable=self.sdk_tools_var)
        self.sdk_tools_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        self._add_placeholder(self.sdk_tools_entry, "e.g., /opt/ti-sdk/bin (optional, uses system tools if empty)")
        ttk.Button(input_frame, text="Browse...", command=self._browse_sdk_tools).grid(row=3, column=2)
        
        # Help text below inputs
        help_label = ttk.Label(input_frame, text="💡 Tip: Binary file is required. Map file & libraries are optional but recommended for detailed analysis.",
                              foreground="#555", font=('TkDefaultFont', 9, 'italic'))
        help_label.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Initialize control variables for analysis options
        self.depth_var = tk.IntVar(value=self.config.get('graph_depth', 5))
        self.layout_var = tk.StringVar(value=self.config.get('layout_algorithm', 'spring'))
        self.show_symbols_var = tk.BooleanVar(value=self.config.get('show_symbols', False))
        
        # === Action Buttons ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        self.generate_btn = ttk.Button(button_frame, text="📊 Generate Report", command=self._analyze_and_generate)
        self.generate_btn.grid(row=0, column=0, padx=5)
        
        # === Progress Bar ===
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # === Status Bar ===
        self.status_var = tk.StringVar()
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # === Build Efficiency Score ===
        self.score_var = tk.StringVar(value="Build Score: --")
        score_label = ttk.Label(main_frame, textvariable=self.score_var, relief=tk.SUNKEN, anchor=tk.E,
                               font=('TkDefaultFont', 9, 'bold'))
        score_label.grid(row=3, column=2, sticky=(tk.W, tk.E))
        
        # === Main Content: Simple Text View ===
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # === Text View for Dependencies ===
        text_frame = ttk.LabelFrame(content_frame, text="Binary Dependencies & Usage", padding="5")
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Scrollable text widget
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.dependency_text = tk.Text(text_frame, wrap=tk.NONE, 
                                       font=('Courier', 10), bg='#F5F5F5',
                                       yscrollcommand=text_scroll.set)
        self.dependency_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_scroll.config(command=self.dependency_text.yview)
        
        # Configure text tags for formatting
        self.dependency_text.tag_configure('binary', foreground='#0000FF', font=('Courier', 11, 'bold'))
        self.dependency_text.tag_configure('library', foreground='#006400', font=('Courier', 10, 'bold'))
        self.dependency_text.tag_configure('used', foreground='#008000')
        self.dependency_text.tag_configure('unused', foreground='#FF0000')
        self.dependency_text.tag_configure('header', foreground='#000080', font=('Courier', 10, 'bold'))
        self.dependency_text.tag_configure('count', foreground='#666666', font=('Courier', 9))
        
        # Show initial message
        self.dependency_text.insert('1.0', '📊 Bin-Xray: Binary Dependency Analyzer\n\n' +
                                   'Developed by: Vinod Kumar Neelakantam\n' +
                                   'https://www.linkedin.com/in/vinodneelakantam/\n\n' +
                                   'Start by entering:\n' +
                                   '  1. Binary file (.elf, .out, .axf)\n' +
                                   '  2. Map file (optional)\n' +
                                   '  3. Library directory (optional)\n\n' +
                                   'Then click "📊 Generate Report" or use --auto flag')
        self._configure_report_text_widget()
        
        # === Signature Footer ===
        signature_frame = tk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=1)
        signature_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        signature_frame.columnconfigure(0, weight=1)
        
        # Developer signature with clickable link
        sig_container = tk.Frame(signature_frame)
        sig_container.grid(row=0, column=0, pady=5)
        
        tk.Label(sig_container, text="Developed by: Vinod Kumar Neelakantam  |  ",
                 foreground='#555555', font=('TkDefaultFont', 9)).grid(row=0, column=0)
        
        # Clickable LinkedIn link
        self.link_label = tk.Label(sig_container, text="https://www.linkedin.com/in/vinodneelakantam/",
                             foreground='#0066CC', font=('TkDefaultFont', 9, 'underline'),
                             cursor='hand2')
        self.link_label.grid(row=0, column=1)
        self.link_label.bind('<Button-1>', lambda e: self._open_linkedin())
        # Hover effect
        self.link_label.bind('<Enter>', lambda e: self.link_label.config(foreground='#0052A3'))
        self.link_label.bind('<Leave>', lambda e: self.link_label.config(foreground='#0066CC'))
    
    def _open_linkedin(self):
        """Open LinkedIn profile in web browser."""
        webbrowser.open('https://www.linkedin.com/in/vinodneelakantam/')
    
    # === File Dialog Methods ===
    
    def _browse_binary(self):
        filename = filedialog.askopenfilename(
            title="Select Binary File",
            filetypes=[("Binary files", "*.elf *.out *.bin *.axf *.exe"), ("All files", "*.*")]
        )
        if filename:
            self.binary_var.set(filename)
    
    def _browse_map(self):
        filename = filedialog.askopenfilename(
            title="Select Map File",
            filetypes=[("Map files", "*.map"), ("All files", "*.*")]
        )
        if filename:
            self.map_var.set(filename)
    
    def _browse_libdir(self):
        dirname = filedialog.askdirectory(title="Select Library Directory")
        if dirname:
            self.libdir_var.set(dirname)
    
    def _browse_sdk_tools(self):
        dirname = filedialog.askdirectory(title="Select SDK Tools Directory")
        if dirname:
            self.sdk_tools_var.set(dirname)
    
    # === Analysis Methods ===
    
    def _analyze_and_generate(self):
        """Main analysis and graph generation method."""
        # Get inputs based on UI type
        if USE_MODERN_UI and hasattr(self, 'ui'):
            inputs = self.ui.get_inputs()
            binary_path = inputs['binary']
            map_path = inputs['map']
            lib_dir = inputs['libdir']
            sdk_tools = inputs['sdk_tools'] or None
        else:
            binary_path = self.binary_var.get()
            map_path = self.map_var.get()
            lib_dir = self.libdir_var.get()
            sdk_tools = self.sdk_tools_var.get() or None
        
        # Save current paths to config
        self.config['last_binary'] = binary_path
        self.config['last_map'] = map_path
        self.config['last_lib_dir'] = lib_dir
        self.config['last_sdk_tools'] = sdk_tools or ''
        if hasattr(self, 'depth_var'):
            self.config['graph_depth'] = self.depth_var.get()
            self.config['layout_algorithm'] = self.layout_var.get()
            self.config['show_symbols'] = self.show_symbols_var.get()
        self._save_config()
        
        # Validate inputs
        if not binary_path and not map_path:
            messagebox.showerror("Error", "Please provide at least a binary or map file.")
            return
        
        # Start progress
        self.progress.start()
        self.generate_btn.config(state='disabled')
        
        # Update status based on UI type
        if hasattr(self, 'ui'):
            self.ui.set_status("Analyzing...")
        self._set_status("Analyzing...")
        self.root.update()
        
        try:
            # Parse binary
            if binary_path and os.path.exists(binary_path):
                self._set_status(f"Parsing binary: {os.path.basename(binary_path)}")
                self.root.update()
                parser = BinaryParser(sdk_tools)
                self.binary_info = parser.parse_binary(binary_path)
            
            # Parse map file
            if map_path and os.path.exists(map_path):
                self._set_status(f"Parsing map file: {os.path.basename(map_path)}")
                self.root.update()
                map_parser = MapFileParser()
                self.map_info = map_parser.parse_map_file(map_path)
            
            # Parse libraries
            self.libraries = {}
            if lib_dir and os.path.isdir(lib_dir):
                self._set_status("Parsing libraries...")
                self.root.update()
                lib_parser = LibraryParser(sdk_tools)
                
                for filename in os.listdir(lib_dir):
                    if filename.endswith(('.a', '.so', '.dll')):
                        lib_path = os.path.join(lib_dir, filename)
                        self.libraries[lib_path] = lib_parser.parse_library(lib_path)
            
            # Build graph
            self._set_status("Building dependency graph...")
            self.root.update()
            depth = self.depth_var.get() if hasattr(self, 'depth_var') else 5
            show_symbols = self.show_symbols_var.get() if hasattr(self, 'show_symbols_var') else False
            self.graph_builder = DependencyGraphBuilder(max_depth=depth)
            self.current_graph = self.graph_builder.build_graph(
                self.binary_info, self.map_info, self.libraries,
                show_symbols=show_symbols
            )
            
            # Visualize
            self._set_status("Rendering graph...")
            self.root.update()
            self._visualize_graph()
            
            # Update unused components panel
            if hasattr(self, '_update_unused_panel'):
                self._update_unused_panel()
            
            # Done
            num_nodes = self.current_graph.number_of_nodes()
            num_edges = self.current_graph.number_of_edges()
            self._set_status(f"Analysis complete: {num_nodes} nodes, {num_edges} edges")
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
            self._set_status("Analysis failed")
            import traceback
            traceback.print_exc()
        finally:
            self.progress.stop()
            self.generate_btn.config(state='normal')
    
    def _visualize_graph(self):
        """Display dependency information organized by static/dynamic libraries."""
        if not self.current_graph or self.current_graph.number_of_nodes() == 0:
            messagebox.showwarning("Warning", "No graph data to visualize.")
            return
        
        self.dependency_text.config(state=tk.NORMAL)
        self.dependency_text.delete('1.0', tk.END)
        
        # Get binary name
        binary_name = self.binary_info.name if self.binary_info else "Binary"
        
        # Get build efficiency score
        score, grade, details = self.graph_builder.get_build_efficiency_score()
        
        # Header with score
        self.dependency_text.insert(tk.END, f"{binary_name}\n", 'binary')
        self.dependency_text.insert(tk.END, f"Build Score: {score:.1f}/100 ({grade})", 'header')
        score_color = 'used' if score >= 70 else 'unused'
        self.dependency_text.insert(tk.END, f" [{details['used_objects']}/{details['total_built_objects']} objects used]\n", score_color)
        self.dependency_text.insert(tk.END, "═" * 80 + "\n", 'header')
        self.dependency_text.insert(tk.END, f"Detailed Summary of unused resources of {binary_name}\n", 'header')
        self.dependency_text.insert(tk.END, "─" * 80 + "\n", 'count')
        self.dependency_text.insert(tk.END, f"Unused libraries: {details['unused_libraries']}\n", 'unused')
        self.dependency_text.insert(tk.END, f"Unused objects: {details['unused_objects']}\n\n", 'unused')
        
        # Collect libraries and objects
        libraries = {}
        objects = []
        shared_libs = []
        
        for node in self.current_graph.nodes():
            node_type = self.graph_builder.node_types.get(node, 'unknown')
            is_unused = self.current_graph.nodes[node].get('unused', False)
            
            if node_type == 'static_lib':
                libraries[node] = {'objects': [], 'unused': is_unused}
            elif node_type == 'shared_lib':
                shared_libs.append((node, is_unused))
            elif node_type == 'object':
                objects.append((node, is_unused))
        
        # Map objects to their libraries
        for u, v, data in self.current_graph.edges(data=True):
            if data.get('type') == 'contains' and u in libraries:
                is_unused = self.current_graph.nodes[v].get('unused', False)
                libraries[u]['objects'].append((v, is_unused))
        
        # Find orphan objects (not in any library)
        orphan_objects = []
        for obj, is_unused in objects:
            found = False
            for lib_name, lib_data in libraries.items():
                if any(o[0] == obj for o in lib_data['objects']):
                    found = True
                    break
            if not found:
                orphan_objects.append((obj, is_unused))
        
        # ========== STATIC LIBRARIES SECTION ==========
        if libraries or orphan_objects:
            self.dependency_text.insert(tk.END, "STATIC LIBRARIES (.a)\n", 'header')
            self.dependency_text.insert(tk.END, "─" * 80 + "\n", 'count')
            
            # Count used/unused
            total_static = len(libraries)
            used_static = sum(1 for lib_data in libraries.values() if not lib_data['unused'])
            
            total_objs = sum(len(lib_data['objects']) for lib_data in libraries.values()) + len(orphan_objects)
            used_objs = sum(sum(1 for _, unused in lib_data['objects'] if not unused) 
                          for lib_data in libraries.values())
            used_objs += sum(1 for _, unused in orphan_objects if not unused)
            
            self.dependency_text.insert(tk.END, 
                f"Libraries: {total_static} total | ", 'count')
            self.dependency_text.insert(tk.END, f"{used_static} used", 'used')
            self.dependency_text.insert(tk.END, " | ", 'count')
            self.dependency_text.insert(tk.END, f"{total_static - used_static} not used\n", 'unused')
            
            self.dependency_text.insert(tk.END, 
                f"Objects: {total_objs} total | ", 'count')
            self.dependency_text.insert(tk.END, f"{used_objs} used", 'used')
            self.dependency_text.insert(tk.END, " | ", 'count')
            self.dependency_text.insert(tk.END, f"{total_objs - used_objs} not used\n\n", 'unused')
            
            # Display static libraries and their objects
            for lib_name in sorted(libraries.keys()):
                lib_data = libraries[lib_name]
                lib_unused = lib_data['unused']
                
                # Library name
                if lib_unused:
                    self.dependency_text.insert(tk.END, f"✗ {lib_name}\n", 'unused')
                else:
                    self.dependency_text.insert(tk.END, f"✓ {lib_name}\n", 'library')
                
                # Objects in this library
                if lib_data['objects']:
                    for obj_name, obj_unused in sorted(lib_data['objects']):
                        if obj_unused:
                            self.dependency_text.insert(tk.END, f"   ✗ {obj_name}\n", 'unused')
                        else:
                            self.dependency_text.insert(tk.END, f"   ✓ {obj_name}\n", 'used')
                
                self.dependency_text.insert(tk.END, "\n")
            
            # Display orphan objects
            if orphan_objects:
                self.dependency_text.insert(tk.END, "Standalone Objects:\n", 'count')
                for obj, is_unused in sorted(orphan_objects):
                    if is_unused:
                        self.dependency_text.insert(tk.END, f"✗ {obj}\n", 'unused')
                    else:
                        self.dependency_text.insert(tk.END, f"✓ {obj}\n", 'used')
                self.dependency_text.insert(tk.END, "\n")
        
        # ========== DYNAMIC LIBRARIES SECTION ==========
        if shared_libs:
            self.dependency_text.insert(tk.END, "DYNAMIC LIBRARIES (.so)\n", 'header')
            self.dependency_text.insert(tk.END, "─" * 80 + "\n", 'count')
            
            used_count = sum(1 for _, unused in shared_libs if not unused)
            
            self.dependency_text.insert(tk.END, 
                f"Total: {len(shared_libs)} | ", 'count')
            self.dependency_text.insert(tk.END, f"{used_count} used", 'used')
            self.dependency_text.insert(tk.END, " | ", 'count')
            self.dependency_text.insert(tk.END, f"{len(shared_libs) - used_count} not used\n\n", 'unused')
            
            for lib, is_unused in sorted(shared_libs):
                if is_unused:
                    self.dependency_text.insert(tk.END, f"✗ {lib}\n", 'unused')
                else:
                    self.dependency_text.insert(tk.END, f"✓ {lib}\n", 'used')
            
            self.dependency_text.insert(tk.END, "\n")
        
        # ========== RECOMMENDATIONS ==========
        total_unused = details['unused_objects'] + details['unused_libraries']
        if total_unused > 0:
            self.dependency_text.insert(tk.END, "\n")
            self.dependency_text.insert(tk.END, "RECOMMENDATIONS - HOW TO REMOVE UNUSED COMPONENTS\n", 'header')
            self.dependency_text.insert(tk.END, "═" * 80 + "\n", 'header')
            
            if details['unused_libraries'] > 0:
                self.dependency_text.insert(tk.END, "\n📦 Unused Libraries:\n", 'count')
                self.dependency_text.insert(tk.END, 
                    "1. Check linker script/command - remove unused .a files from link list\n"
                    "2. Update Makefile LIBS variable to exclude them\n"
                    "3. Example: Remove '-lhal' from LDFLAGS if libhal.a is unused\n"
                    "4. For CMake: Remove target_link_libraries(app unused_lib)\n\n", 'count')
            
            if details['unused_objects'] > 0:
                self.dependency_text.insert(tk.END, "🔧 Unused Objects:\n", 'count')
                
                # Count orphan vs library-contained
                orphan_unused = sum(1 for _, unused in orphan_objects if unused)
                lib_contained_unused = details['unused_objects'] - orphan_unused
                
                if orphan_unused > 0:
                    self.dependency_text.insert(tk.END, 
                        f"\n  Orphaned Objects ({orphan_unused} files):\n"
                        "  → These are compiled but never archived into .a or linked\n"
                        "  → Fix: Update Makefile to exclude from build:\n"
                        "     - Remove from SOURCES or OBJS list\n"
                        "     - Add to .gitignore if generated\n"
                        "     - Example: SOURCES := $(filter-out unused.c, $(SOURCES))\n\n", 'count')
                
                if lib_contained_unused > 0:
                    self.dependency_text.insert(tk.END, 
                        f"  Objects in Unused Libraries ({lib_contained_unused} files):\n"
                        "  → These are inside .a files that aren't linked\n"
                        "  → Fix: Remove parent library (see above)\n"
                        "  → Or: If library is used but objects aren't, linker handles it\n\n", 'count')
            
            self.dependency_text.insert(tk.END, "💡 Quick Wins:\n", 'count')
            self.dependency_text.insert(tk.END, 
                "• Run 'make clean' to verify - unused objects shouldn't rebuild\n"
                "• Check for legacy code - old modules no longer needed\n"
                "• Look for debug/test code compiled in release builds\n"
                "• Use conditional compilation: #ifdef DEBUG / #endif\n"
                "• Benefits: Faster builds, smaller binaries, cleaner codebase\n\n", 'count')
            
            # Calculate potential time savings
            if total_unused > 5:
                savings_pct = (details['unused_objects'] / details['total_built_objects'] * 100) if details['total_built_objects'] > 0 else 0
                self.dependency_text.insert(tk.END, f"⏱️  Potential Build Time Reduction: ~{savings_pct:.1f}%\n", 'unused' if savings_pct > 20 else 'used')
        else:
            self.dependency_text.insert(tk.END, "\n")
            self.dependency_text.insert(tk.END, "✅ PERFECT BUILD - NO CLEANUP NEEDED!\n", 'used')
            self.dependency_text.insert(tk.END, "All compiled components are used in the final binary.\n", 'count')
        
        # Legend
        self.dependency_text.insert(tk.END, "\n" + "─" * 80 + "\n", 'count')
        self.dependency_text.insert(tk.END, "Legend: ", 'header')
        self.dependency_text.insert(tk.END, "✓ = Used (green)  ", 'used')
        self.dependency_text.insert(tk.END, "✗ = Unused (red)\n", 'unused')
        
        self._configure_report_text_widget()
        self.dependency_text.yview_moveto(0)
    
    def _update_unused_panel(self):
        """Update build efficiency score in status bar."""
        if not self.graph_builder:
            return
        
        score, grade, details = self.graph_builder.get_build_efficiency_score()
        score_text = f"Build Score: {score}/100 ({grade})"
        
        # Update score in status bar or modern UI
        if hasattr(self, 'score_var'):
            self.score_var.set(score_text)
        
        # Update modern UI stats
        if hasattr(self, 'ui'):
            self._update_stats(score=f"{score:.0f}%")
            
            # Count libraries and objects (used/total)
            all_libs = [n for n in self.current_graph.nodes() if n.endswith(('.a', '.so', '.dll'))]
            all_objs = [n for n in self.current_graph.nodes() if n.endswith('.o')]
            
            # Count used vs total
            used_libs = len([n for n in all_libs if self.current_graph.out_degree(n) > 0 or self.current_graph.in_degree(n) > 0])
            used_objs = len([n for n in all_objs if self.current_graph.out_degree(n) > 0 or self.current_graph.in_degree(n) > 0])
            
            self._update_stats(
                libs=f"{used_libs}/{len(all_libs)}" if all_libs else "0/0",
                objs=f"{used_objs}/{len(all_objs)}" if all_objs else "0/0"
            )
    
    def _apply_filter(self):
        """Filter nodes based on search term."""
        if not self.graph_builder:
            return
        
        filter_text = self.filter_var.get().lower()
        if not filter_text:
            self._reset_filter()
            return
        
        # Find matching nodes
        matching_nodes = [node for node in self.graph_builder.graph.nodes()
                         if filter_text in node.lower()]
        
        if matching_nodes:
            # Create subgraph with matching nodes and their neighbors
            all_nodes = set()
            for node in matching_nodes:
                all_nodes.add(node)
                all_nodes.update(self.graph_builder.graph.predecessors(node))
                all_nodes.update(self.graph_builder.graph.successors(node))
            
            self.current_graph = self.graph_builder.graph.subgraph(all_nodes).copy()
            self._visualize_graph()
            self.status_var.set(f"Filtered: {len(matching_nodes)} matching nodes")
        else:
            messagebox.showinfo("Filter", f"No nodes matching '{filter_text}'")
    
    def _reset_filter(self):
        """Reset to full graph."""
        if self.graph_builder:
            self.current_graph = self.graph_builder.graph
            self._visualize_graph()
            self.filter_var.set('')
            self.status_var.set("Filter reset")
    
    def _clear_graph(self):
        """Clear the current graph display without clearing input fields."""
        self.dependency_text.config(state=tk.NORMAL)
        self.dependency_text.delete('1.0', tk.END)
        self.dependency_text.insert('1.0', 
                                    'Enter input files and click\n"Analyze & Generate Graph"\nto view dependencies')
        self.dependency_text.config(state=tk.DISABLED)
        
        self.builder = DependencyGraphBuilder()
        self.current_graph = None
        self.status_var.set("Graph cleared. Input files preserved. Ready to analyze.")
    
    def _clear_inputs(self):
        """Clear all input fields and graph."""
        self.binary_var.set('')
        self.map_var.set('')
        self.libdir_var.set('')
        self.sdk_tools_var.set('')
        self.filter_var.set('')
        self._clear_graph()
        self.status_var.set("All inputs cleared")
    
    def _reset_view(self):
        """Reset text view to top."""
        if self.current_graph:
            self.dependency_text.yview_moveto(0)
    
    def _show_node_details(self):
        """Show detailed information about graph nodes."""
        if not self.graph_builder:
            messagebox.showinfo("Info", "No graph data available.")
            return
        
        # Create a new window with node details
        details_window = tk.Toplevel(self.root)
        details_window.title("Node Details")
        details_window.geometry("600x400")
        
        # Create text widget
        text = scrolledtext.ScrolledText(details_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        # Write node information
        text.insert(tk.END, "=== Node Details ===\n\n")
        
        for node in sorted(self.graph_builder.graph.nodes()):
            node_type = self.graph_builder.node_types.get(node, 'unknown')
            details = self.graph_builder.node_details.get(node, {})
            
            text.insert(tk.END, f"Node: {node}\n")
            text.insert(tk.END, f"Type: {node_type}\n")
            
            for key, value in details.items():
                text.insert(tk.END, f"  {key}: {value}\n")
            
            # Show connections
            in_degree = self.graph_builder.graph.in_degree(node)
            out_degree = self.graph_builder.graph.out_degree(node)
            text.insert(tk.END, f"  Dependencies: {out_degree}, Dependents: {in_degree}\n")
            text.insert(tk.END, "\n")
        
        text.config(state=tk.DISABLED)
    
    # === Export Methods ===
    
    def _export_graph(self, format: str):
        """Export graph as image."""
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format}",
            filetypes=[(f"{format.upper()} files", f"*.{format}")]
        )
        
        if filename:
            try:
                self.fig.savefig(filename, format=format, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Graph exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    def _copy_report_modern(self):
        """Copy report to clipboard (modern UI version)."""
        report_text = self.dependency_text.get('1.0', tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(report_text)
        if hasattr(self, 'ui'):
            self.ui.set_status("✓ Report copied to clipboard")
            self.root.after(3000, lambda: self.ui.set_status("Ready"))
    
    def _export_report_modern(self):
        """Export report to file (modern UI version)."""
        if not self.binary_info:
            messagebox.showwarning("Warning", "No report to export.")
            return
        
        default_name = f"{self.binary_info.name}_dependency_report.txt"
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Dependency Report"
        )
        
        if filename:
            try:
                report_text = self.dependency_text.get('1.0', tk.END)
                with open(filename, 'w') as f:
                    f.write(report_text)
                if hasattr(self, 'ui'):
                    self.ui.set_status(f"✓ Report exported to {os.path.basename(filename)}")
                messagebox.showinfo("Export Successful", f"Report saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export report:\n{str(e)}")
    
    def _show_unused_report(self):
        """Show detailed report of unused objects and libraries."""
        if not self.graph_builder:
            messagebox.showwarning("Warning", "Please analyze a binary first.")
            return
        
        unused_summary = self.graph_builder.get_unused_summary()
        
        if unused_summary['total_unused'] == 0:
            messagebox.showinfo("Unused Analysis", 
                              "✅ No unused objects or libraries detected!\n\n"
                              "All built components are referenced by the binary.")
            return
        
        # Create detailed report window
        report_window = tk.Toplevel(self.root)
        report_window.title("Unused Objects & Libraries Report")
        report_window.geometry("700x500")
        
        # Add text widget with scrollbar
        text_frame = ttk.Frame(report_window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                      font=('Courier', 10))
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        
        # Build report
        report = "=" * 70 + "\n"
        report += "UNUSED OBJECTS & LIBRARIES REPORT\n"
        report += "=" * 70 + "\n\n"
        
        report += f"📊 SUMMARY\n"
        report += f"  Total Unused: {unused_summary['total_unused']}\n"
        report += f"  - Unused Libraries: {len(unused_summary['unused_libraries'])}\n"
        report += f"  - Unused Objects: {len(unused_summary['unused_objects'])}\n\n"
        
        report += "⚠️  These files are built but NOT linked/referenced by the binary.\n"
        report += "They may be:\n"
        report += "  • Dead code that can be removed\n"
        report += "  • Optional components not enabled in this build\n"
        report += "  • Test/debug modules excluded from release\n"
        report += "  • Plugins/modules loaded dynamically at runtime\n\n"
        
        if unused_summary['unused_libraries']:
            report += "-" * 70 + "\n"
            report += f"📚 UNUSED LIBRARIES ({len(unused_summary['unused_libraries'])})\n"
            report += "-" * 70 + "\n"
            report += "These static/shared libraries are present in the library directory\n"
            report += "but NO symbols from them are referenced by the final binary.\n\n"
            
            for lib in unused_summary['unused_libraries']:
                report += f"  ❌ {lib}\n"
                
                # Check if it's a static library
                if lib.endswith('.a'):
                    report += f"     Type: Static Library (.a)\n"
                    report += f"     → None of its object files are linked into binary\n"
                    report += f"     → Not listed in linker command or not needed\n"
                elif lib.endswith('.so') or '.so.' in lib:
                    report += f"     Type: Shared Library (.so)\n"
                    report += f"     → Binary doesn't have NEEDED entry for this lib\n"
                    report += f"     → Not used at load time\n"
                
                report += f"     Impact: Can remove from deployment\n"
                
                # Estimate size savings
                if self.graph_builder.node_details.get(lib):
                    details = self.graph_builder.node_details[lib]
                    if 'size' in details:
                        size_kb = details['size'] / 1024
                        report += f"     Size: {size_kb:.1f} KB\n"
                
                report += "\n"
        
        if unused_summary['unused_objects']:
            report += "-" * 70 + "\n"
            report += f"🔧 UNUSED OBJECT FILES ({len(unused_summary['unused_objects'])})\n"
            report += "-" * 70 + "\n"
            report += "These object files are compiled but none of their symbols\n"
            report += "are referenced by the binary or other used modules.\n\n"
            
            for obj in unused_summary['unused_objects']:
                report += f"  ❌ {obj}\n"
                report += f"     → No functions/symbols referenced by binary\n"
                report += f"     → All symbols are unused/unreachable\n"
                report += f"     → Consider removing from build system\n\n"
        
        report += "=" * 70 + "\n"
        report += "💡 RECOMMENDATIONS\n"
        report += "=" * 70 + "\n\n"
        
        if unused_summary['unused_libraries']:
            report += "For Unused Libraries:\n"
            report += "  1. Check if needed for dynamic/runtime loading\n"
            report += "  2. Remove from linker flags (-l) if not needed\n"
            report += "  3. Remove from deployment package/installation\n"
            report += "  4. Update build scripts (Makefile/CMake/etc.)\n\n"
        
        if unused_summary['unused_objects']:
            report += "For Unused Objects:\n"
            report += "  1. Verify source files aren't needed\n"
            report += "  2. Remove from compilation list\n"
            report += "  3. Archive as dead code if uncertain\n"
            report += "  4. Update build dependency graphs\n\n"
        
        total_unused = len(unused_summary['unused_libraries']) + len(unused_summary['unused_objects'])
        report += f"Potential Actions:\n"
        report += f"  • Review all {total_unused} unused components\n"
        report += f"  • Reduce build time by skipping unused files\n"
        report += f"  • Reduce binary size (for static libs)\n"
        report += f"  • Simplify deployment (for shared libs)\n"
        
        text.insert('1.0', report)
        text.config(state=tk.DISABLED)
        
        # Add close button
        ttk.Button(report_window, text="Close", 
                  command=report_window.destroy).pack(pady=10)
    
    def _export_graphml(self):
        """Export graph as GraphML file."""
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".graphml",
            filetypes=[("GraphML files", "*.graphml")]
        )
        
        if filename:
            try:
                nx.write_graphml(self.current_graph, filename)
                messagebox.showinfo("Success", f"Graph exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    # === Help Methods ===
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """Bin-Xray - Binary Dependency Analyzer
        
Version: 1.0

Developed by:
Vinod Kumar Neelakantam
https://www.linkedin.com/in/vinodneelakantam/

A tool for visualizing dependency relationships in 
embedded SDK build outputs, particularly for 
automotive/ADAS SDKs.

Features:
• Parse ELF binaries and libraries
• Analyze linker map files
• Build dependency graphs
• Interactive visualization
• Export capabilities
        """
        messagebox.showinfo("About Bin-Xray", about_text)
    
    def _show_required_tools(self):
        """Show required external tools."""
        tools_text = """Required System Tools:

The following tools are used for binary analysis:

• readelf - Read ELF file information
• nm - List symbols from object files
• objdump - Display object file information
• ar - Archive utility (for .a files)
• file - Determine file type
• ldd - Print shared library dependencies (optional)

Installation:

Ubuntu/Debian:
  sudo apt-get install binutils file

Fedora/RHEL:
  sudo dnf install binutils file

macOS:
  brew install binutils

For embedded toolchains, specify the SDK tools 
directory containing toolchain-specific versions:
  - arm-none-eabi-readelf
  - tiarm-nm
  - etc.
        """
        messagebox.showinfo("Required Tools", tools_text)


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main application entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Bin-Xray: Binary Dependency Visualization Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch empty GUI
  python3 bin_xray.py
  
  # Pre-load ADAS test files
  python3 bin_xray.py \\
    --binary test_binaries/adas_camera/adas_camera.elf \\
    --map test_binaries/adas_camera/adas_camera.map \\
    --libdir test_binaries/adas_camera/ \\
    --show-symbols \\
    --layout hierarchical
        """
    )
    
    parser.add_argument('--binary', '-b', 
                        help='Path to binary/ELF file to analyze')
    parser.add_argument('--map', '-m',
                        help='Path to map file')
    parser.add_argument('--libdir', '-l',
                        help='Path to library directory')
    parser.add_argument('--show-symbols', '-s', action='store_true',
                        help='Enable symbol dependency visualization')
    parser.add_argument('--layout', '-L', 
                        choices=['spring', 'circular', 'kamada_kawai', 'shell', 'hierarchical'],
                        default='spring',
                        help='Graph layout algorithm (default: spring)')
    parser.add_argument('--depth', '-d', type=int, default=5,
                        help='Maximum dependency depth (default: 5)')
    parser.add_argument('--auto', '-a', action='store_true',
                        help='Automatically analyze after loading files')
    
    args = parser.parse_args()
    
    if not TKINTER_AVAILABLE:
        print("Error: tkinter is not available. Please install tkinter to run the GUI.")
        print("On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("On Fedora: sudo dnf install python3-tkinter")
        print("On macOS: tkinter should be included with Python")
        return 1
    
    root = tk.Tk()
    app = BinXrayGUI(root)
    
    # Pre-fill fields from command-line arguments (handle both modern and legacy UI)
    if args.binary:
        if hasattr(app, 'ui'):
            app.ui.binary_input.set(args.binary)
        elif hasattr(app, 'binary_var'):
            app.binary_var.set(args.binary)
    
    if args.map:
        if hasattr(app, 'ui'):
            app.ui.map_input.set(args.map)
        elif hasattr(app, 'map_var'):
            app.map_var.set(args.map)
    
    if args.libdir:
        if hasattr(app, 'ui'):
            app.ui.libdir_input.set(args.libdir)
        elif hasattr(app, 'libdir_var'):
            app.libdir_var.set(args.libdir)
    
    # Only set these for legacy UI (modern UI doesn't have these options exposed yet)
    if hasattr(app, 'show_symbols_var') and args.show_symbols:
        app.show_symbols_var.set(True)
    if hasattr(app, 'layout_var') and args.layout:
        app.layout_var.set(args.layout)
    if hasattr(app, 'depth_var') and args.depth:
        app.depth_var.set(args.depth)
    
    # Auto-analyze if requested
    if args.auto and args.binary:
        # Schedule analysis after GUI is fully initialized
        root.after(500, app._analyze_and_generate)
    
    root.mainloop()


if __name__ == '__main__':
    main()
