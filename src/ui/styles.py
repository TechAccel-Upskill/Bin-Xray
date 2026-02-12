"""
Modern UI Styling for Bin-Xray
Provides color schemes, fonts, and styling constants
"""

# Color Palette - Dark Professional Theme
COLORS = {
    # Primary colors - vibrant cyan/teal
    'primary': '#06B6D4',          # Bright cyan
    'primary_hover': '#0891B2',    # Darker cyan
    'primary_dark': '#0E7490',     # Deep cyan
    'primary_light': '#22D3EE',    # Light cyan
    'primary_gradient_start': '#06B6D4',
    'primary_gradient_end': '#14B8A6',  # Teal gradient
    
    # Secondary colors - emerald accent
    'secondary': '#10B981',        # Emerald green
    'secondary_hover': '#059669',
    'accent_purple': '#A78BFA',    # Soft purple
    'accent_pink': '#F472B6',      # Soft pink
    'accent_orange': '#FB923C',    # Soft orange
    
    # Status colors
    'success': '#10B981',
    'warning': '#FBBF24',
    'error': '#F87171',
    'info': '#60A5FA',
    
    # Backgrounds - dark theme
    'bg_main': '#0F172A',          # Deep navy
    'bg_secondary': '#1E293B',     # Slate gray
    'bg_card': '#1E293B',          # Card background
    'bg_sidebar': '#0F172A',       # Sidebar
    'bg_gradient_start': '#0F172A',
    'bg_gradient_end': '#1E293B',
    'bg_hover': '#334155',         # Hover state
    'bg_active': '#164E63',        # Active with cyan tint
    
    # Borders and shadows
    'border_light': '#1E293B',     # Subtle border
    'border': '#334155',           # Medium border
    'border_medium': '#475569',    # Visible border
    'border_accent': '#06B6D4',    # Accent border
    'shadow_sm': 'rgba(0,0,0,0.3)',
    'shadow_md': 'rgba(0,0,0,0.5)',
    'shadow_lg': 'rgba(0,0,0,0.7)',
    
    # Text colors - light on dark
    'text_primary': '#F1F5F9',     # Almost white
    'text_secondary': '#94A3B8',   # Light gray
    'text_muted': '#64748B',       # Muted gray
    'text_white': '#FFFFFF',
    'text_link': '#22D3EE',        # Cyan link
    
    # Component specific
    'input_bg': '#1E293B',
    'input_border': '#334155',
    'input_focus': '#06B6D4',
    'input_focus_ring': '#155E75',
    
    # Badge colors - dark theme
    'badge_blue': '#1E3A8A',
    'badge_blue_text': '#93C5FD',
    'badge_green': '#064E3B',
    'badge_green_text': '#6EE7B7',
    'badge_purple': '#4C1D95',
    'badge_purple_text': '#C4B5FD',
    
    # Report colors
    'used': '#10B981',
    'unused': '#F87171',
    'header': '#06B6D4',
    'library': '#A78BFA',
}

# Fonts - Modern system fonts
FONTS = {
    'heading_large': ('Inter', 20, 'bold'),
    'heading': ('Inter', 14, 'bold'),
    'subheading': ('Inter', 12, 'bold'),
    'section_title': ('Inter', 11, 'normal'),
    'body': ('Inter', 10),
    'body_bold': ('Inter', 10, 'bold'),
    'small': ('Inter', 9),
    'small_italic': ('Inter', 9, 'italic'),
    'label': ('Inter', 9, 'bold'),
    'monospace': ('JetBrains Mono', 10),
    'monospace_bold': ('JetBrains Mono', 10, 'bold'),
    'link': ('Inter', 9, 'underline'),
    'emoji': ('DejaVu Sans', 12),  # Better emoji support on Linux
}

# Padding and spacing - Generous dark theme spacing
SPACING = {
    'xs': 8,
    'sm': 12,
    'md': 16,
    'lg': 20,
    'xl': 24,
    'xxl': 32,
    'section': 24,      # Space between sections
    'card': 20,         # Card internal padding
    'card_gap': 16,     # Gap between cards
}

# Border radius (simulated with relief styles)
BORDER = {
    'radius': 4,
    'width': 1,
}

# Component heights - Modern proportions
HEIGHTS = {
    'button': 40,           # Modern comfortable button
    'button_sm': 32,        # Small button
    'input': 42,            # Comfortable input
    'card_header': 48,      # Spacious header
    'section_badge': 28,    # Section badge height
}

# Button Styles - Dark theme with vibrant accents
BUTTON_STYLES = {
    'primary': {
        'bg': '#06B6D4',
        'fg': '#FFFFFF',
        'hover_bg': '#0891B2',
        'active_bg': '#0E7490',
        'border': '#06B6D4',
    },
    'secondary': {
        'bg': '#334155',
        'fg': '#F1F5F9',
        'hover_bg': '#475569',
        'active_bg': '#64748B',
        'border': '#475569',
    },
    'outline': {
        'bg': '#1E293B',
        'fg': '#06B6D4',
        'hover_bg': '#164E63',
        'active_bg': '#155E75',
        'border': '#06B6D4',
    },
    'ghost': {
        'bg': '#1E293B',
        'fg': '#94A3B8',
        'hover_bg': '#334155',
        'active_bg': '#475569',
        'border': '#334155',
    },
}

# Border radius - modern rounded corners
BORDER_RADIUS = {
    'sm': 6,
    'md': 8,
    'lg': 12,
    'xl': 16,
    'full': 999,
}

# Icons (emoji-based for simplicity)
ICONS = {
    'file': '📄',
    'folder': '📁',
    'settings': '⚙️',
    'chart': '📊',
    'check': '✓',
    'cross': '✗',
    'warning': '⚠️',
    'info': 'ℹ️',
    'report': '📋',
    'export': '💾',
    'refresh': '🔄',
    'search': '🔍',
    'link': '🔗',
    'binary': '🔧',
    'library': '📚',
    'success': '✅',
    'error': '❌',
}

# Card styles
CARD_STYLE = {
    'bg': COLORS['bg_card'],
    'border': COLORS['border'],
    'shadow': '#0000001A',  # 10% opacity black
    'padding': SPACING['md'],
    'radius': 8,
}

# Status badge colors
STATUS_COLORS = {
    'A+': '#10B981',  # Green
    'A': '#10B981',
    'B': '#3B82F6',   # Blue
    'C': '#F59E0B',   # Orange
    'D': '#F59E0B',
    'F': '#EF4444',   # Red
}

def get_status_color(grade):
    """Get color for a build score grade."""
    return STATUS_COLORS.get(grade, COLORS['text_secondary'])
