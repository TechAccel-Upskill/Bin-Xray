#!/usr/bin/env python3
"""
Bin-Xray: Binary Dependency Analyzer for Embedded Systems

Core analysis engine: parse ELF binaries, linker map files, and static
libraries to build a dependency graph and surface unused objects/libraries.

Author: Generated for embedded systems development
License: MIT
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
import json
import platform

import networkx as nx




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

