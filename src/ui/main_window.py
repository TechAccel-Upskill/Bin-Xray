"""
Modern Main Window for Bin-Xray
Enhanced UI/UX with modern design patterns
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from pathlib import Path

from . import styles
from . import (
    COLORS, FONTS, SPACING, ICONS,
    ModernButton, Card, FloatingCard, InputField, InfoCard, StatCard,
    HeaderBar, SectionHeader, SectionBadge
)


class ModernMainWindow:
    """Modern main window with improved UI/UX."""
    
    def __init__(self, root, config, callbacks):
        """
        Initialize the modern UI.
        
        Args:
            root: Tkinter root window
            config: Configuration dictionary
            callbacks: Dictionary of callback functions
        """
        self.root = root
        self.config = config
        self.callbacks = callbacks
        
        # Configure root window
        self.root.title("Bin-Xray - Binary Dependency Analyzer")
        self.root.geometry("1400x900")
        self.root.configure(bg=styles.COLORS['bg_main'])
        
        # Configure ttk styles for VS Code look
        self._configure_styles()
        
        # Create UI
        self._create_ui()
    
    def _configure_styles(self):
        """Configure ttk styles for a VS Code appearance."""
        style = ttk.Style()
        
        # Scrollbar styling - thin VS Code style
        style.configure('Vertical.TScrollbar',
                       background=COLORS['bg_sidebar'],
                       troughcolor=COLORS['bg_sidebar'],
                       borderwidth=0,
                       arrowsize=12)
        
        # Progressbar styling
        style.configure('TProgressbar',
                       background=COLORS['primary'],
                       troughcolor=COLORS['bg_secondary'],
                       borderwidth=0,
                       thickness=4)
    
    def _create_ui(self):
        """Create modern dashboard-style UI layout."""
        # Main container
        self.main_container = tk.Frame(self.root, bg=COLORS['bg_main'])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top navigation bar
        self._create_top_nav()
        
        # Main content with tabs
        self._create_tabbed_interface()
        
        # Status bar at bottom
        self._create_status_bar()
    
    def _create_top_nav(self):
        """Create modern top navigation bar."""
        nav = tk.Frame(self.main_container, bg=COLORS['primary'], height=60)
        nav.pack(fill=tk.X)
        nav.pack_propagate(False)
        
        # Left side - Logo and title
        left_section = tk.Frame(nav, bg=COLORS['primary'])
        left_section.pack(side=tk.LEFT, padx=SPACING['xl'], pady=SPACING['md'])
        
        title = tk.Label(
            left_section,
            text="⚡ Bin-Xray",
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['primary'],
            fg=COLORS['text_white']
        )
        title.pack(side=tk.LEFT)
        
        subtitle = tk.Label(
            left_section,
            text="Binary Dependency Analyzer",
            font=FONTS['small'],
            bg=COLORS['primary'],
            fg=COLORS['text_white']
        )
        subtitle.pack(side=tk.LEFT, padx=(SPACING['md'], 0))
        
        # Right side - Generate Report button
        right_section = tk.Frame(nav, bg=COLORS['primary'])
        right_section.pack(side=tk.RIGHT, padx=SPACING['xl'], pady=SPACING['md'])
        
        # Generate Report button (primary action)
        self.nav_generate_btn = ModernButton(
            right_section,
            text="Generate Report",
            icon="🚀",
            style_type='secondary',
            command=lambda: self.callbacks['analyze']()
        )
        self.nav_generate_btn.pack(side=tk.RIGHT)
        
        # Alias for backward compatibility
        self.generate_btn = self.nav_generate_btn
    
    def _create_header(self):
        """Create modern header bar."""
        pass  # Replaced by top nav
    
    def _create_tabbed_interface(self):
        """Create modern tabbed interface."""
        # Tab container
        tab_container = tk.Frame(self.main_container, bg=COLORS['bg_main'])
        tab_container.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook with custom styling
        style = ttk.Style()
        style.theme_use('default')
        
        # Custom tab styling
        style.configure('TNotebook', background=COLORS['bg_main'], borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=COLORS['bg_secondary'],
                       foreground=COLORS['text_secondary'],
                       padding=[20, 10],
                       font=FONTS['body_bold'])
        style.map('TNotebook.Tab',
                 background=[('selected', COLORS['bg_main'])],
                 foreground=[('selected', COLORS['primary'])])
        
        self.notebook = ttk.Notebook(tab_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Create single session tab
        self.session_tab = tk.Frame(self.notebook, bg=COLORS['bg_main'])
        
        self.notebook.add(self.session_tab, text="  📊 Session 1  ")
        
        # Populate session tab with setup and results
        self._create_session_tab()
    
    def _create_session_tab(self):
        """Create Session 1 tab with setup and results combined."""
        # Main scrollable container
        canvas = tk.Canvas(self.session_tab, bg=COLORS['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.session_tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=COLORS['bg_main'])
        
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add padding
        tk.Frame(content, bg=COLORS['bg_main'], height=SPACING['lg']).pack()
        
        # === TWO COLUMN LAYOUT: Left (Config + Stats) | Right (Detailed Report) ===
        main_layout = tk.Frame(content, bg=COLORS['bg_main'])
        main_layout.pack(fill=tk.BOTH, expand=True, padx=(SPACING['xxl'], SPACING['xxl']))
        
        # Configure grid weights - right column gets much more space when expanding
        main_layout.columnconfigure(0, weight=1, minsize=450)  # Left column - minimum width
        main_layout.columnconfigure(1, weight=5)  # Right column - takes 5x more extra space
        main_layout.rowconfigure(0, weight=1)
        
        # Left column - Configuration + Stats
        left_column = tk.Frame(main_layout, bg=COLORS['bg_main'])
        left_column.grid(row=0, column=0, sticky='nsew', padx=(0, SPACING['md']))
        
        # Right column - Detailed Report
        right_column = tk.Frame(main_layout, bg=COLORS['bg_main'])
        right_column.grid(row=0, column=1, sticky='nsew', padx=(SPACING['md'], 0))
        
        # Create left side content
        self._create_left_column(left_column)
        
        # Create right side content
        self._create_right_column(right_column)
        
        # Bottom padding
        tk.Frame(content, bg=COLORS['bg_main'], height=SPACING['xl']).pack()
    
    def _create_left_column(self, parent):
        """Create left column with Configuration and Stats."""
        # Configuration header
        header = tk.Frame(parent, bg=COLORS['bg_main'])
        header.pack(fill=tk.X, pady=(0, SPACING['lg']))
        
        tk.Label(
            header,
            text="⚙️ Configuration",
            font=('Inter', 18, 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        # === TWO COLUMN LAYOUT ===
        columns = tk.Frame(parent, bg=COLORS['bg_main'])
        columns.pack(fill=tk.BOTH, expand=True, padx=SPACING['xxl'])
        
        # Left column
        left_col = tk.Frame(columns, bg=COLORS['bg_main'])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['md']))
        
        # Right column
        right_col = tk.Frame(columns, bg=COLORS['bg_main'])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(SPACING['md'], 0))
        
        # === LEFT COLUMN - ALL INPUT FIELDS ===
        # Required Files Card
        req_card = FloatingCard(left_col, title="📁 Required Files")
        req_card.pack(fill=tk.X, pady=(0, SPACING['lg']))
        
        # Binary File with inline browse button
        bin_frame = tk.Frame(req_card.body, bg=COLORS['bg_card'])
        bin_frame.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        bin_input_frame = tk.Frame(bin_frame, bg=COLORS['bg_card'])
        bin_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['sm']))
        
        self.binary_input = InputField(
            bin_input_frame,
            label="Binary File",
            placeholder="Select binary file (.elf, .out, etc.)"
        )
        self.binary_input.pack(fill=tk.X)
        if self.config.get('last_binary'):
            self.binary_input.set(self.config['last_binary'])
        
        browse_bin = ModernButton(
            bin_frame,
            text="📂",
            style_type='outline',
            command=self._browse_binary
        )
        browse_bin.pack(side=tk.RIGHT, pady=(20, 0))
        
        # Linker Map File with inline browse button
        map_frame = tk.Frame(req_card.body, bg=COLORS['bg_card'])
        map_frame.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        map_input_frame = tk.Frame(map_frame, bg=COLORS['bg_card'])
        map_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['sm']))
        
        self.map_input = InputField(
            map_input_frame,
            label="Linker Map File",
            placeholder=".map file for detailed analysis"
        )
        self.map_input.pack(fill=tk.X)
        if self.config.get('last_map'):
            self.map_input.set(self.config['last_map'])
        
        browse_map = ModernButton(
            map_frame,
            text="📂",
            style_type='outline',
            command=self._browse_map
        )
        browse_map.pack(side=tk.RIGHT, pady=(20, 0))
        
        # Library Directory with inline browse button
        lib_frame = tk.Frame(req_card.body, bg=COLORS['bg_card'])
        lib_frame.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        lib_input_frame = tk.Frame(lib_frame, bg=COLORS['bg_card'])
        lib_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['sm']))
        
        self.libdir_input = InputField(
            lib_input_frame,
            label="Library Directory",
            placeholder="Path to shared libraries"
        )
        self.libdir_input.pack(fill=tk.X)
        if self.config.get('last_lib_dir'):
            self.libdir_input.set(self.config['last_lib_dir'])
        
        browse_lib = ModernButton(
            lib_frame,
            text="Browse",
            style_type='outline',
            command=self._browse_libdir
        )
        browse_lib.pack(side=tk.RIGHT, pady=(20, 0))
        
        # SDK Tools with inline browse button
        sdk_frame_left = tk.Frame(req_card.body, bg=COLORS['bg_card'])
        sdk_frame_left.pack(fill=tk.X)
        
        sdk_input_frame_left = tk.Frame(sdk_frame_left, bg=COLORS['bg_card'])
        sdk_input_frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['sm']))
        
        self.sdk_tools_input = InputField(
            sdk_input_frame_left,
            label="SDK Tools Path (Optional)",
            placeholder="Leave empty to use system tools"
        )
        self.sdk_tools_input.pack(fill=tk.X)
        if self.config.get('last_sdk_tools'):
            self.sdk_tools_input.set(self.config['last_sdk_tools'])
        
        browse_sdk_left = ModernButton(
            sdk_frame_left,
            text="Browse",
            style_type='outline',
            command=self._browse_sdk_tools
        )
        browse_sdk_left.pack(side=tk.RIGHT, pady=(20, 0))
        
        # === STATS SECTION ===
        stats_header = tk.Frame(parent, bg=COLORS['bg_main'])
        stats_header.pack(fill=tk.X, pady=(SPACING['xl'], SPACING['md']))
        
        tk.Label(
            stats_header,
            text="📊 Analysis Results",
            font=('Inter', 18, 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        stats_card = FloatingCard(parent, title="Statistics")
        stats_card.pack(fill=tk.X)
        
        # Build Efficiency
        self.score_card = StatCard(
            stats_card.body,
            icon="📊",
            title="Build Efficiency Score",
            value="--",
            color='primary'
        )
        self.score_card.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        # Libraries
        self.libs_card = StatCard(
            stats_card.body,
            icon="📚",
            title="Libraries (Used/Detected)",
            value="0/0",
            color='success'
        )
        self.libs_card.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        # Objects
        self.objs_card = StatCard(
            stats_card.body,
            icon="🔧",
            title="Objects (Used/Detected)",
            value="0/0",
            color='purple'
        )
        self.objs_card.pack(fill=tk.X)
    
    def _create_right_column(self, parent):
        """Create right column with Detailed Report (full height from top)."""
        bin_frame = tk.Frame(req_card.body, bg=COLORS['bg_card'])
        bin_frame.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        bin_input_frame = tk.Frame(bin_frame, bg=COLORS['bg_card'])
        bin_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['sm']))
        
        self.binary_input = InputField(
            bin_input_frame,
            label="Binary File",
            placeholder="Select binary file (.elf, .out, etc.)"
        )
        self.binary_input.pack(fill=tk.X)
        if self.config.get('last_binary'):
            self.binary_input.set(self.config['last_binary'])
        
        browse_bin = ModernButton(
            bin_frame,
            text="Browse",
            style_type='outline',
            command=self._browse_binary
        )
        browse_bin.pack(side=tk.RIGHT, pady=(20, 0))
        
        # Linker Map File with inline browse button
        map_frame = tk.Frame(req_card.body, bg=COLORS['bg_card'])
        map_frame.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        map_input_frame = tk.Frame(map_frame, bg=COLORS['bg_card'])
        map_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['sm']))
        
        self.map_input = InputField(
            map_input_frame,
            label="Linker Map File",
            placeholder=".map file for detailed analysis"
        )
        self.map_input.pack(fill=tk.X)
        if self.config.get('last_map'):
            self.map_input.set(self.config['last_map'])
        
        browse_map = ModernButton(
            map_frame,
            text="Browse",
            style_type='outline',
            command=self._browse_map
        )
        browse_map.pack(side=tk.RIGHT, pady=(20, 0))
        
        # Library Directory with inline browse button
        lib_frame = tk.Frame(req_card.body, bg=COLORS['bg_card'])
        lib_frame.pack(fill=tk.X)
        
        lib_input_frame = tk.Frame(lib_frame, bg=COLORS['bg_card'])
        lib_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['sm']))
        
        self.libdir_input = InputField(
            lib_input_frame,
            label="Library Directory",
            placeholder="Path to shared libraries"
        )
        self.libdir_input.pack(fill=tk.X)
        if self.config.get('last_lib_dir'):
            self.libdir_input.set(self.config['last_lib_dir'])
        
        browse_lib = ModernButton(
            lib_frame,
            text="�",
            style_type='outline',
            command=self._browse_libdir
        )
        browse_lib.pack(side=tk.RIGHT, pady=(20, 0))
        
        # === RIGHT COLUMN ===
        # Advanced Settings Card
        adv_card = FloatingCard(right_col, title="⚙️ Advanced Settings")
        adv_card.pack(fill=tk.X, pady=(0, SPACING['lg']))
        
        # SDK Tools with inline browse button
        sdk_frame = tk.Frame(adv_card.body, bg=COLORS['bg_card'])
        sdk_frame.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        sdk_input_frame = tk.Frame(sdk_frame, bg=COLORS['bg_card'])
        sdk_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING['sm']))
        
        self.sdk_tools_input = InputField(
            sdk_input_frame,
            label="SDK Tools Path",
            placeholder="Leave empty to use system tools"
        )
        self.sdk_tools_input.pack(fill=tk.X)
        if self.config.get('last_sdk_tools'):
            self.sdk_tools_input.set(self.config['last_sdk_tools'])
        
        browse_sdk = ModernButton(
            sdk_frame,
            text="�",
            style_type='outline',
            command=self._browse_sdk_tools
        )
        browse_sdk.pack(side=tk.RIGHT, pady=(20, 0))
        
        # === ANALYSIS RESULTS (in right column) ===
        # Note: Stats cards will be created in _create_stats_cards method
        # and placed in the parent container, appearing below both columns
    
    def _create_right_column(self, parent):
        """Create right column with Detailed Report (full height from top)."""
        # Report header
        report_header = tk.Frame(parent, bg=COLORS['bg_main'])
        report_header.pack(fill=tk.X, pady=(0, SPACING['lg']))
        
        tk.Label(
            report_header,
            text="📋 Detailed Report",
            font=('Inter', 18, 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        # Toolbar with export buttons
        toolbar = tk.Frame(parent, bg=COLORS['bg_main'])
        toolbar.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        export_frame = tk.Frame(toolbar, bg=COLORS['bg_main'])
        export_frame.pack(side=tk.RIGHT)
        
        ModernButton(
            export_frame, text="Copy", icon="📋", style_type='ghost',
            command=lambda: self.callbacks.get('copy_report', lambda: None)()
        ).pack(side=tk.LEFT, padx=(0, SPACING['sm']))
        
        ModernButton(
            export_frame, text="Export", icon="💾", style_type='outline',
            command=lambda: self.callbacks.get('export_report', lambda: None)()
        ).pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        # Report display card (full height)
        report_card = FloatingCard(parent)
        report_card.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbars
        text_scroll_y = ttk.Scrollbar(report_card.body)
        text_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_scroll_x = ttk.Scrollbar(report_card.body, orient='horizontal')
        text_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.report_text = tk.Text(
            report_card.body, font=FONTS['monospace'], bg=COLORS['bg_card'], 
            fg=COLORS['text_primary'], wrap=tk.NONE,
            yscrollcommand=text_scroll_y.set, xscrollcommand=text_scroll_x.set,
            relief=tk.FLAT, borderwidth=0, padx=SPACING['md'], pady=SPACING['md']
        )
        self.report_text.pack(fill=tk.BOTH, expand=True)
        
        text_scroll_y.config(command=self.report_text.yview)
        text_scroll_x.config(command=self.report_text.xview)
        
        # Configure text tags for colored output
        self.report_text.tag_config('header', foreground=COLORS['header'], font=FONTS['monospace_bold'])
        self.report_text.tag_config('binary', foreground=COLORS['primary'])
        self.report_text.tag_config('library', foreground=COLORS['library'])
        self.report_text.tag_config('used', foreground=COLORS['used'])
        self.report_text.tag_config('unused', foreground=COLORS['unused'])
        self.report_text.tag_config('count', foreground=COLORS['warning'])
        
        # Initial message
        self.report_text.insert('1.0', "No analysis run yet.\n\nClick 'Generate Report' in the top right corner to analyze your binary.")
        self.report_text.config(state=tk.DISABLED)
    
    
    def _create_analysis_results_section(self, parent):
        """Create Analysis Results section with stats cards and detailed report."""
        # Results header
        results_header = tk.Frame(parent, bg=COLORS['bg_main'])
        results_header.pack(fill=tk.X, padx=SPACING['xxl'], pady=(0, SPACING['lg']))
        
        tk.Label(
            results_header,
            text="📊 Analysis Results",
            font=('Inter', 18, 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        # Main container
        main_container = tk.Frame(parent, bg=COLORS['bg_main'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING['xxl'], pady=(0, SPACING['lg']))
        
        # === STATS CARDS (Horizontal Row at Top) ===
        stats_row = tk.Frame(main_container, bg=COLORS['bg_main'])
        stats_row.pack(fill=tk.X, pady=(0, SPACING['lg']))
        
        # Configure 3 columns with equal weight
        stats_row.columnconfigure(0, weight=1)
        stats_row.columnconfigure(1, weight=1)
        stats_row.columnconfigure(2, weight=1)
        
        # Build Efficiency
        self.score_card = StatCard(
            stats_row,
            icon="📊",
            title="Build Efficiency Score",
            value="--",
            color='primary'
        )
        self.score_card.grid(row=0, column=0, sticky='ew', padx=(0, SPACING['sm']))
        
        # Libraries
        self.libs_card = StatCard(
            stats_row,
            icon="📚",
            title="Libraries (Used/Detected)",
            value="0/0",
            color='success'
        )
        self.libs_card.grid(row=0, column=1, sticky='ew', padx=(SPACING['sm'], SPACING['sm']))
        
        # Objects
        self.objs_card = StatCard(
            stats_row,
            icon="🔧",
            title="Objects (Used/Detected)",
            value="0/0",
            color='purple'
        )
        self.objs_card.grid(row=0, column=2, sticky='ew', padx=(SPACING['sm'], 0))
        
        # === DETAILED REPORT (Full Width Below Stats) ===
        report_container = tk.Frame(main_container, bg=COLORS['bg_main'])
        report_container.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = tk.Frame(report_container, bg=COLORS['bg_main'])
        toolbar.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        tk.Label(
            toolbar,
            text="📋 Detailed Report",
            font=FONTS['heading'],
            bg=COLORS['bg_main'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        # Export buttons on right
        export_frame = tk.Frame(toolbar, bg=COLORS['bg_main'])
        export_frame.pack(side=tk.RIGHT)
        
        copy_btn = ModernButton(
            export_frame,
            text="Copy",
            icon="📋",
            style_type='ghost',
            command=lambda: self.callbacks.get('copy_report', lambda: None)()
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, SPACING['sm']))
        
        export_btn = ModernButton(
            export_frame,
            text="Export",
            icon="💾",
            style_type='outline',
            command=lambda: self.callbacks.get('export_report', lambda: None)()
        )
        export_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(report_container, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        # Report display card
        report_card = FloatingCard(report_container)
        report_card.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbars
        text_scroll_y = ttk.Scrollbar(report_card.body)
        text_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_scroll_x = ttk.Scrollbar(report_card.body, orient='horizontal')
        text_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.report_text = tk.Text(
            report_card.body,
            font=FONTS['monospace'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary'],
            wrap=tk.NONE,
            yscrollcommand=text_scroll_y.set,
            xscrollcommand=text_scroll_x.set,
            relief=tk.FLAT,
            borderwidth=0,
            padx=SPACING['md'],
            pady=SPACING['md'],
            height=20
        )
        self.report_text.pack(fill=tk.BOTH, expand=True)
        
        text_scroll_y.config(command=self.report_text.yview)
        text_scroll_x.config(command=self.report_text.xview)
        
        # Configure text tags for colored output
        self.report_text.tag_config('header', foreground=COLORS['header'], font=FONTS['monospace_bold'])
        self.report_text.tag_config('binary', foreground=COLORS['primary'])
        self.report_text.tag_config('library', foreground=COLORS['library'])
        self.report_text.tag_config('used', foreground=COLORS['used'])
        self.report_text.tag_config('unused', foreground=COLORS['unused'])
        self.report_text.tag_config('count', foreground=COLORS['warning'])
        
        # Initial message
        self.report_text.insert('1.0', "No analysis run yet.\n\nClick 'Generate Report' in the top right corner to analyze your binary.")
        self.report_text.config(state=tk.DISABLED)
    
    def _create_results_section(self, parent):
        """Create detailed report section (full width). DEPRECATED - Use _create_analysis_results_section instead."""
        # === DETAILED REPORT - FULL WIDTH ===
        # Report container
        report_container = tk.Frame(parent, bg=COLORS['bg_main'])
        report_container.pack(fill=tk.BOTH, expand=True, padx=SPACING['xxl'], pady=(0, SPACING['lg']))
        
        # Toolbar
        toolbar = tk.Frame(report_container, bg=COLORS['bg_main'])
        toolbar.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        tk.Label(
            toolbar,
            text="📋 Detailed Report",
            font=FONTS['heading'],
            bg=COLORS['bg_main'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        # Export buttons on right
        export_frame = tk.Frame(toolbar, bg=COLORS['bg_main'])
        export_frame.pack(side=tk.RIGHT)
        
        copy_btn = ModernButton(
            export_frame,
            text="Copy",
            icon="📋",
            style_type='ghost',
            command=lambda: self.callbacks.get('copy_report', lambda: None)()
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, SPACING['sm']))
        
        export_btn = ModernButton(
            export_frame,
            text="Export",
            icon="💾",
            style_type='outline',
            command=lambda: self.callbacks.get('export_report', lambda: None)()
        )
        export_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(report_container, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, SPACING['md']))
        
        # Report display card
        report_card = FloatingCard(report_container)
        report_card.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbars
        text_scroll_y = ttk.Scrollbar(report_card.body)
        text_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_scroll_x = ttk.Scrollbar(report_card.body, orient='horizontal')
        text_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.report_text = tk.Text(
            report_card.body,
            font=FONTS['monospace'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary'],
            wrap=tk.NONE,
            yscrollcommand=text_scroll_y.set,
            xscrollcommand=text_scroll_x.set,
            relief=tk.FLAT,
            borderwidth=0,
            padx=SPACING['md'],
            pady=SPACING['md'],
            height=20
        )
        self.report_text.pack(fill=tk.BOTH, expand=True)
        
        text_scroll_y.config(command=self.report_text.yview)
        text_scroll_x.config(command=self.report_text.xview)
        
        # Configure text tags for colored output
        self.report_text.tag_config('header', foreground=COLORS['header'], font=FONTS['monospace_bold'])
        self.report_text.tag_config('binary', foreground=COLORS['primary'])
        self.report_text.tag_config('library', foreground=COLORS['library'])
        self.report_text.tag_config('used', foreground=COLORS['used'])
        self.report_text.tag_config('unused', foreground=COLORS['unused'])
        self.report_text.tag_config('count', foreground=COLORS['warning'])
        
        # Initial message
        self.report_text.insert('1.0', "No analysis run yet.\n\nClick 'Generate Report' in the top right corner to analyze your binary.")
        self.report_text.config(state=tk.DISABLED)
    
    def _create_dashboard_tab(self):
        """Create dashboard tab with statistics overview."""
        # Scrollable container
        canvas = tk.Canvas(self.dashboard_tab, bg=COLORS['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dashboard_tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=COLORS['bg_main'])
        
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add padding
        tk.Frame(content, bg=COLORS['bg_main'], height=SPACING['xl']).pack()
        
        # Dashboard header
        header = tk.Frame(content, bg=COLORS['bg_main'])
        header.pack(fill=tk.X, padx=SPACING['xxl'], pady=(0, SPACING['lg']))
        
        tk.Label(
            header,
            text="📊 Analysis Dashboard",
            font=('Inter', 20, 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        # Stats grid - 3 columns
        stats_grid = tk.Frame(content, bg=COLORS['bg_main'])
        stats_grid.pack(fill=tk.X, padx=SPACING['xxl'], pady=(0, SPACING['lg']))
        
        # Configure grid weights
        for i in range(3):
            stats_grid.columnconfigure(i, weight=1)
        
        # Build Efficiency
        self.score_card = StatCard(
            stats_grid,
            icon="📊",
            title="Build Efficiency Score",
            value="--",
            color='primary'
        )
        self.score_card.grid(row=0, column=0, sticky='ew', padx=(0, SPACING['md']))
        
        # Libraries
        self.libs_card = StatCard(
            stats_grid,
            icon="📚",
            title="Libraries (Used/Detected)",
            value="0/0",
            color='success'
        )
        self.libs_card.grid(row=0, column=1, sticky='ew', padx=(SPACING['sm'], SPACING['sm']))
        
        # Objects
        self.objs_card = StatCard(
            stats_grid,
            icon="🔧",
            title="Objects (Used/Detected)",
            value="0/0",
            color='purple'
        )
        self.objs_card.grid(row=0, column=2, sticky='ew', padx=(SPACING['md'], 0))
        
        # Additional info cards
        info_section = tk.Frame(content, bg=COLORS['bg_main'])
        info_section.pack(fill=tk.BOTH, expand=True, padx=SPACING['xxl'], pady=(SPACING['lg'], SPACING['xl']))
        
        # Recent Analysis Card
        recent_card = FloatingCard(info_section, title="📝 Recent Analysis")
        recent_card.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING['md']))
        
        placeholder_text = tk.Label(
            recent_card.body,
            text="No analysis performed yet.\
\
Run an analysis from the Setup tab to see results here.",
            font=FONTS['body'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_secondary'],
            justify=tk.CENTER
        )
        placeholder_text.pack(expand=True, pady=SPACING['xxl'])
    
    def _create_status_bar(self):
        """Create modern status bar at bottom."""
        status_bar = tk.Frame(self.main_container, bg=COLORS['bg_secondary'], height=32)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        # Status text
        self.status_label = tk.Label(
            status_bar,
            text="Ready",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary'],
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=SPACING['md'], pady=SPACING['xs'])
        
        # Version info on right
        version_label = tk.Label(
            status_bar,
            text="v1.0.0",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted'],
            anchor=tk.E
        )
        version_label.pack(side=tk.RIGHT, padx=SPACING['md'], pady=SPACING['xs'])
    
    def _create_footer(self):
        """Footer - deprecated, using status bar instead."""
        pass
    
    def _create_main_content(self, parent):
        """Old method - replaced by tabbed interface."""
        pass  # Now using tabs - content moved to _create_results_tab()
    
    def _show_welcome_message(self):
        """Deprecated - welcome message now shown in results tab."""
        pass
    
    def _create_footer(self):
        """Create footer with developer info."""
        footer = tk.Frame(self.main_container, bg=COLORS['bg_secondary'], height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        # Content
        content = tk.Frame(footer, bg=COLORS['bg_secondary'])
        content.pack(expand=True)
        
        # Developer info
        dev_label = tk.Label(
            content,
            text="Developed by: Vinod Kumar Neelakantam",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        )
        dev_label.pack(side=tk.LEFT, padx=SPACING['xs'])
        
        # Separator
        sep_label = tk.Label(
            content,
            text="|",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted']
        )
        sep_label.pack(side=tk.LEFT, padx=SPACING['xs'])
        
        # LinkedIn link
        link_label = tk.Label(
            content,
            text="🔗 LinkedIn Profile",
            font=FONTS['link'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['primary'],
            cursor='hand2'
        )
        link_label.pack(side=tk.LEFT, padx=SPACING['xs'])
        link_label.bind('<Button-1>', lambda e: webbrowser.open('https://www.linkedin.com/in/vinodneelakantam/'))
        link_label.bind('<Enter>', lambda e: link_label.config(fg=COLORS['primary_hover']))
        link_label.bind('<Leave>', lambda e: link_label.config(fg=COLORS['primary']))
    
    # File dialog methods
    def _browse_binary(self):
        """Browse for binary file."""
        filename = filedialog.askopenfilename(
            title="Select Binary File",
            filetypes=[
                ("Binary files", "*.elf *.out *.bin *.axf *.exe"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.binary_input.set(filename)
    
    def _browse_map(self):
        """Browse for map file."""
        filename = filedialog.askopenfilename(
            title="Select Map File",
            filetypes=[("Map files", "*.map"), ("All files", "*.*")]
        )
        if filename:
            self.map_input.set(filename)
    
    def _browse_libdir(self):
        """Browse for library directory."""
        dirname = filedialog.askdirectory(title="Select Library Directory")
        if dirname:
            self.libdir_input.set(dirname)
    
    def _browse_sdk_tools(self):
        """Browse for SDK tools directory."""
        dirname = filedialog.askdirectory(title="Select SDK Tools Directory")
        if dirname:
            self.sdk_tools_input.set(dirname)
    
    # Public methods for external control
    def get_inputs(self):
        """Get all input values."""
        return {
            'binary': self.binary_input.get(),
            'map': self.map_input.get(),
            'libdir': self.libdir_input.get(),
            'sdk_tools': self.sdk_tools_input.get(),
        }
    
    def set_status(self, status, color=None):
        """Update status label."""
        self.status_label.config(text=status)
        if color:
            self.status_label.config(fg=color)
    
    def update_stats(self, score=None, libs=None, objs=None):
        """Update statistics cards."""
        if score is not None:
            # Extract grade from score string like "85.5% (B)"
            grade = score.split('(')[-1].rstrip(')') if '(' in score else ''
            color = styles.get_status_color(grade) if grade else COLORS['text_primary']
            self.score_card.update_value(score, color)
        
        if libs is not None:
            self.libs_card.update_value(str(libs))
        
        if objs is not None:
            self.objs_card.update_value(str(objs))
    
    def start_progress(self):
        """Start progress bar animation."""
        self.progress.start()
        self.generate_btn.config(state=tk.DISABLED)
    
    def stop_progress(self):
        """Stop progress bar animation."""
        self.progress.stop()
        self.generate_btn.config(state=tk.NORMAL)
