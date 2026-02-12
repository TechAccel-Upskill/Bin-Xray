#!/usr/bin/env python3
"""
Example usage of Bin-Xray for different SDK scenarios.
"""

import os
import sys

# Add parent directory to path to import bin_xray
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bin_xray import BinaryParser, MapFileParser, LibraryParser, DependencyGraphBuilder

# ==============================================================================
# Example 1: Analyze a single ELF binary
# ==============================================================================

def example_simple_binary():
    """Simplest use case: analyze a single binary."""
    print("=== Example 1: Simple Binary Analysis ===\n")
    
    # Replace with your binary path
    binary_path = "/path/to/your/application.elf"
    
    if not os.path.exists(binary_path):
        print(f"Binary not found: {binary_path}")
        print("Please update the path in this example.")
        return
    
    # Create parser (no SDK tools needed for basic analysis)
    parser = BinaryParser()
    
    # Parse the binary
    binary_info = parser.parse_binary(binary_path)
    
    # Print results
    print(f"Binary: {binary_info.name}")
    print(f"Format: {binary_info.format}")
    print(f"Architecture: {binary_info.architecture}")
    print(f"Dynamic dependencies: {len(binary_info.dynamic_deps)}")
    for dep in binary_info.dynamic_deps:
        print(f"  - {dep}")
    
    print(f"\nDefined symbols: {len(binary_info.defined_symbols)}")
    print(f"Undefined symbols: {len(binary_info.undefined_symbols)}")
    
    # Show first few symbols
    print("\nFirst 10 defined symbols:")
    for sym in binary_info.defined_symbols[:10]:
        print(f"  {sym.type} {sym.name} @ 0x{sym.address:08x} (size: {sym.size})")
    
    print()


# ==============================================================================
# Example 2: Parse linker map file
# ==============================================================================

def example_map_file():
    """Parse a linker map file to extract cross-references."""
    print("=== Example 2: Map File Analysis ===\n")
    
    map_path = "/path/to/your/application.map"
    
    if not os.path.exists(map_path):
        print(f"Map file not found: {map_path}")
        print("Please update the path in this example.")
        return
    
    # Create map parser
    map_parser = MapFileParser()
    
    # Parse map file
    map_info = map_parser.parse_map_file(map_path)
    
    # Print results
    print(f"Map file: {os.path.basename(map_path)}")
    print(f"Memory regions: {len(map_info.memory_regions)}")
    for region, details in map_info.memory_regions.items():
        origin = details.get('origin', 0)
        length = details.get('length', 0)
        print(f"  {region}: 0x{origin:08x} - 0x{origin+length:08x} ({length} bytes)")
    
    print(f"\nSections: {len(map_info.section_map)}")
    for section, objects in list(map_info.section_map.items())[:5]:
        print(f"  {section}: {len(objects)} object files")
    
    print(f"\nSymbol cross-references: {len(map_info.symbol_xref)}")
    
    # Show some cross-references
    print("\nFirst 5 symbol cross-references:")
    for i, (symbol, refs) in enumerate(map_info.symbol_xref.items()):
        if i >= 5:
            break
        defined = ', '.join(refs.get('defined_by', []))
        used = ', '.join(refs.get('used_by', [])[:3])
        print(f"  {symbol}")
        print(f"    Defined in: {defined}")
        print(f"    Used by: {used}")
    
    print()


# ==============================================================================
# Example 3: TI Jacinto SDK Project
# ==============================================================================

def example_ti_jacinto():
    """Example for TI Jacinto TDA4VM SDK project."""
    print("=== Example 3: TI Jacinto SDK Analysis ===\n")
    
    # Typical TI Jacinto SDK paths
    sdk_root = "/path/to/ti/jacinto-sdk"
    project = "vision_apps"
    build = "out/J7/A72/LINUX/Release"
    
    binary_path = os.path.join(sdk_root, project, build, "vx_app.out")
    map_path = os.path.join(sdk_root, project, build, "vx_app.map")
    lib_dir = os.path.join(sdk_root, project, build, "lib")
    sdk_tools = "/opt/ti/ti-cgt-armllvm_2.1.0.LTS/bin"
    
    print(f"SDK Root: {sdk_root}")
    print(f"Binary: {binary_path}")
    print(f"Map: {map_path}")
    print(f"Libraries: {lib_dir}")
    print(f"Tools: {sdk_tools}")
    print()
    
    if not os.path.exists(binary_path):
        print("Note: Update paths to match your TI SDK installation")
        return
    
    # Parse with TI tools
    parser = BinaryParser(sdk_tools_path=sdk_tools)
    binary_info = parser.parse_binary(binary_path)
    
    print(f"Detected tools:")
    for tool, path in parser.tools.items():
        print(f"  {tool}: {path}")
    
    print(f"\nBinary info:")
    print(f"  Architecture: {binary_info.architecture}")
    print(f"  Symbols: {len(binary_info.defined_symbols)}")
    
    # Parse map file
    map_parser = MapFileParser()
    map_info = map_parser.parse_map_file(map_path)
    
    print(f"\nMap file sections: {len(map_info.section_map)}")
    
    # Build dependency graph
    graph_builder = DependencyGraphBuilder(max_depth=5)
    graph = graph_builder.build_graph(binary_info, map_info)
    
    print(f"\nDependency graph:")
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")
    
    print()


# ==============================================================================
# Example 4: Complete workflow with graph building
# ==============================================================================

def example_complete_workflow():
    """Complete workflow: binary + map + libraries -> graph."""
    print("=== Example 4: Complete Workflow ===\n")
    
    # Input files
    binary_path = "/path/to/application.elf"
    map_path = "/path/to/application.map"
    lib_dir = "/path/to/libraries"
    
    # Parse binary
    print("Step 1: Parsing binary...")
    parser = BinaryParser()
    binary_info = parser.parse_binary(binary_path) if os.path.exists(binary_path) else None
    
    if binary_info:
        print(f"  ✓ Binary parsed: {binary_info.name}")
    else:
        print(f"  ✗ Binary not found")
    
    # Parse map file
    print("\nStep 2: Parsing map file...")
    map_parser = MapFileParser()
    map_info = map_parser.parse_map_file(map_path) if os.path.exists(map_path) else None
    
    if map_info:
        print(f"  ✓ Map parsed: {len(map_info.section_map)} sections")
    else:
        print(f"  ✗ Map file not found")
    
    # Parse libraries
    print("\nStep 3: Parsing libraries...")
    libraries = {}
    
    if os.path.isdir(lib_dir):
        lib_parser = LibraryParser()
        
        for filename in os.listdir(lib_dir):
            if filename.endswith(('.a', '.so')):
                lib_path = os.path.join(lib_dir, filename)
                libraries[lib_path] = lib_parser.parse_library(lib_path)
                print(f"  ✓ Parsed: {filename}")
    else:
        print(f"  ✗ Library directory not found")
    
    # Build graph
    print("\nStep 4: Building dependency graph...")
    graph_builder = DependencyGraphBuilder(max_depth=6)
    graph = graph_builder.build_graph(binary_info, map_info, libraries)
    
    print(f"  ✓ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Analyze graph
    print("\nStep 5: Analyzing graph...")
    
    # Find most connected nodes
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())
    
    print("\n  Most dependent nodes (most dependencies):")
    sorted_out = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)
    for node, degree in sorted_out[:5]:
        print(f"    {node}: {degree} dependencies")
    
    print("\n  Most depended upon nodes (most dependents):")
    sorted_in = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
    for node, degree in sorted_in[:5]:
        print(f"    {node}: {degree} dependents")
    
    # Export graph
    print("\nStep 6: Exporting graph...")
    
    try:
        import networkx as nx
        
        # Export as GraphML
        output_file = "dependency_graph.graphml"
        nx.write_graphml(graph, output_file)
        print(f"  ✓ Exported to {output_file}")
        
        # Export as DOT (if pygraphviz available)
        try:
            dot_file = "dependency_graph.dot"
            nx.drawing.nx_pydot.write_dot(graph, dot_file)
            print(f"  ✓ Exported to {dot_file}")
        except:
            print(f"  ⓘ pydot not available, skipping DOT export")
    
    except Exception as e:
        print(f"  ✗ Export failed: {e}")
    
    print()


# ==============================================================================
# Example 5: Programmatic filtering
# ==============================================================================

def example_graph_filtering():
    """Filter and analyze specific parts of the dependency graph."""
    print("=== Example 5: Graph Filtering ===\n")
    
    # Build a sample graph (in real use, load from parsed data)
    import networkx as nx
    
    G = nx.MultiDiGraph()
    
    # Add sample nodes
    G.add_node("app.elf", type="binary")
    G.add_node("libmath.so", type="shared_lib")
    G.add_node("libdriver.a", type="static_lib")
    G.add_node("driver.o", type="object")
    G.add_node("utils.o", type="object")
    
    # Add edges
    G.add_edge("app.elf", "libmath.so", type="dynamic")
    G.add_edge("app.elf", "libdriver.a", type="link")
    G.add_edge("libdriver.a", "driver.o", type="contains")
    G.add_edge("driver.o", "utils.o", type="symbol_ref", symbol="init_hardware")
    
    print(f"Full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Filter 1: Only shared libraries
    print("\nFilter 1: Only shared libraries")
    shared_libs = [n for n in G.nodes() if G.nodes[n].get('type') == 'shared_lib']
    print(f"  Found: {shared_libs}")
    
    # Filter 2: Subgraph around a specific node
    print("\nFilter 2: Subgraph around 'driver.o'")
    if 'driver.o' in G:
        neighbors = set([n for n in G.predecessors('driver.o')])
        neighbors.update([n for n in G.successors('driver.o')])
        neighbors.add('driver.o')
        
        subgraph = G.subgraph(neighbors)
        print(f"  Subgraph: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")
        print(f"  Nodes: {list(subgraph.nodes())}")
    
    # Filter 3: Find all symbol references
    print("\nFilter 3: Find all symbol reference edges")
    symbol_edges = [(u, v, data) for u, v, data in G.edges(data=True) 
                    if data.get('type') == 'symbol_ref']
    print(f"  Found {len(symbol_edges)} symbol references")
    for u, v, data in symbol_edges:
        symbol = data.get('symbol', 'unknown')
        print(f"    {u} -> {v} (symbol: {symbol})")
    
    print()


# ==============================================================================
# Main
# ==============================================================================

def main():
    """Run all examples."""
    
    examples = [
        ("Simple Binary", example_simple_binary),
        ("Map File", example_map_file),
        ("TI Jacinto SDK", example_ti_jacinto),
        ("Complete Workflow", example_complete_workflow),
        ("Graph Filtering", example_graph_filtering),
    ]
    
    print("Bin-Xray Usage Examples\n")
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nNote: Update file paths in the examples before running.")
    print("\nTo run a specific example, modify this script or import the functions.\n")
    
    # Uncomment to run specific examples:
    # example_simple_binary()
    # example_map_file()
    # example_ti_jacinto()
    # example_complete_workflow()
    example_graph_filtering()  # This one works without real files


if __name__ == '__main__':
    main()
