"""
Modern UI Components for Bin-Xray
Reusable custom widgets with modern styling
"""

import tkinter as tk
from tkinter import ttk
from . import styles

class ModernButton(tk.Button):
    """Modern button with rounded corners and smooth interactions."""
    
    def __init__(self, parent, text="", command=None, style_type='primary', icon='', **kwargs):
        self.style_type = style_type
        btn_style = styles.BUTTON_STYLES[style_type]
        
        # Format text with icon
        display_text = f"{icon}  {text}" if icon else text
        
        super().__init__(
            parent,
            text=display_text,
            command=command,
            bg=btn_style['bg'],
            fg=btn_style['fg'],
            font=styles.FONTS['body_bold'],
            relief=tk.FLAT,
            borderwidth=0,
            padx=styles.SPACING['lg'],
            pady=styles.SPACING['sm'],
            cursor='hand2',
            activebackground=btn_style.get('active_bg', btn_style['bg']),
            activeforeground=btn_style['fg'],
            **kwargs
        )
        
        # Border for non-primary buttons
        if style_type in ['secondary', 'outline']:
            self.config(
                highlightbackground=btn_style.get('border', styles.COLORS['border']),
                highlightcolor=styles.COLORS['input_focus'],
                highlightthickness=1
            )
        
        # Hover effects
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        btn_style = styles.BUTTON_STYLES[self.style_type]
        self.config(bg=btn_style.get('hover_bg', btn_style['bg']))
    
    def _on_leave(self, event):
        btn_style = styles.BUTTON_STYLES[self.style_type]
        self.config(bg=btn_style['bg'])


class SectionBadge(tk.Frame):
    """Modern section badge with icon and colored background."""
    
    def __init__(self, parent, title='', icon='', color='primary', **kwargs):
        super().__init__(parent, bg=styles.COLORS['bg_sidebar'], **kwargs)
        
        # Badge colors
        badge_colors = {
            'primary': (styles.COLORS['badge_blue'], styles.COLORS['badge_blue_text']),
            'success': (styles.COLORS['badge_green'], styles.COLORS['badge_green_text']),
            'purple': (styles.COLORS['badge_purple'], styles.COLORS['badge_purple_text']),
        }
        bg_color, text_color = badge_colors.get(color, badge_colors['primary'])
        
        # Badge container
        badge = tk.Frame(self, bg=bg_color, height=styles.HEIGHTS['section_badge'])
        badge.pack(fill=tk.X, pady=(0, styles.SPACING['sm']))
        
        # Content
        content = tk.Frame(badge, bg=bg_color)
        content.pack(fill=tk.X, padx=styles.SPACING['md'], pady=styles.SPACING['xs'])
        
        # Icon
        if icon:
            icon_label = tk.Label(
                content,
                text=icon,
                font=('Segoe UI', 14),
                bg=bg_color,
                fg=text_color
            )
            icon_label.pack(side=tk.LEFT, padx=(0, styles.SPACING['sm']))
        
        # Title
        title_label = tk.Label(
            content,
            text=title.upper(),
            font=styles.FONTS['section_title'],
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(side=tk.LEFT)


class SectionHeader(tk.Frame):
    """Clean minimal section header."""
    
    def __init__(self, parent, title='', icon='', **kwargs):
        super().__init__(parent, bg=styles.COLORS['bg_sidebar'], **kwargs)
        
        # Simple text header
        title_text = f"{icon}  {title}" if icon else title
        title_label = tk.Label(
            self,
            text=title_text,
            font=styles.FONTS['subheading'],
            bg=styles.COLORS['bg_sidebar'],
            fg=styles.COLORS['text_primary'],
            anchor=tk.W
        )
        title_label.pack(fill=tk.X, pady=(0, styles.SPACING['sm']))


class FloatingCard(tk.Frame):
    """Modern floating card with shadow and rounded appearance."""
    
    def __init__(self, parent, title='', **kwargs):
        super().__init__(parent, bg=styles.COLORS['bg_sidebar'], **kwargs)
        
        # Shadow layer (simulated with multiple borders)
        shadow = tk.Frame(self, bg='#E5E7EB')
        shadow.pack(fill=tk.BOTH, expand=True, padx=(0, 1), pady=(0, 2))
        
        # Card container
        card = tk.Frame(shadow, bg='#F3F4F6')
        card.pack(fill=tk.BOTH, expand=True, padx=(0, 1), pady=(0, 1))
        
        # Inner card
        inner = tk.Frame(card, bg=styles.COLORS['bg_card'])
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        if title:
            # Card header with bottom border
            header = tk.Frame(inner, bg=styles.COLORS['bg_card'])
            header.pack(fill=tk.X, padx=styles.SPACING['card'], pady=(styles.SPACING['md'], 0))
            
            title_label = tk.Label(
                header,
                text=title,
                font=styles.FONTS['subheading'],
                bg=styles.COLORS['bg_card'],
                fg=styles.COLORS['text_primary'],
                anchor=tk.W
            )
            title_label.pack(fill=tk.X, pady=(0, styles.SPACING['sm']))
            
            # Accent line
            accent = tk.Frame(inner, bg=styles.COLORS['primary'], height=2)
            accent.pack(fill=tk.X, padx=styles.SPACING['card'])
        
        # Card body
        self.body = tk.Frame(inner, bg=styles.COLORS['bg_card'])
        self.body.pack(fill=tk.BOTH, expand=True, 
                      padx=styles.SPACING['card'], 
                      pady=styles.SPACING['card'])


class Card(tk.Frame):
    """Simple modern card with subtle border."""
    
    def __init__(self, parent, title='', accent_color=None, **kwargs):
        super().__init__(parent, bg=styles.COLORS['bg_sidebar'], **kwargs)
        
        # Card border
        border = tk.Frame(self, bg=styles.COLORS['border'])
        border.pack(fill=tk.BOTH, expand=True)
        
        # Inner container
        inner = tk.Frame(border, bg=styles.COLORS['bg_card'])
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        if title:
            # Card header
            header = tk.Frame(inner, bg=styles.COLORS['bg_card'])
            header.pack(fill=tk.X, padx=styles.SPACING['card'], 
                       pady=(styles.SPACING['md'], 0))
            
            title_label = tk.Label(
                header,
                text=title,
                font=styles.FONTS['subheading'],
                bg=styles.COLORS['bg_card'],
                fg=styles.COLORS['text_primary'],
                anchor=tk.W
            )
            title_label.pack(fill=tk.X, pady=(0, styles.SPACING['sm']))
            
            # Optional colored accent bar
            if accent_color:
                accent = tk.Frame(inner, bg=accent_color, height=2)
                accent.pack(fill=tk.X, padx=styles.SPACING['card'])
        
        # Card body
        self.body = tk.Frame(inner, bg=styles.COLORS['bg_card'])
        self.body.pack(fill=tk.BOTH, expand=True,
                      padx=styles.SPACING['card'],
                      pady=styles.SPACING['card'])


class ModernInput(tk.Frame):
    """Modern input field with focus ring and clean design."""
    
    def __init__(self, parent, label='', placeholder='', **kwargs):
        super().__init__(parent, bg=styles.COLORS['bg_card'])
        
        # Label
        if label:
            label_widget = tk.Label(
                self,
                text=label,
                font=styles.FONTS['label'],
                bg=styles.COLORS['bg_card'],
                fg=styles.COLORS['text_secondary'],
                anchor=tk.W
            )
            label_widget.pack(fill=tk.X, pady=(0, styles.SPACING['xs']))
        
        # Focus ring container (for blue glow effect)
        self.focus_ring = tk.Frame(self, bg=styles.COLORS['input_border'])
        self.focus_ring.pack(fill=tk.X)
        
        # Entry container
        entry_container = tk.Frame(self.focus_ring, bg=styles.COLORS['input_bg'])
        entry_container.pack(fill=tk.X, padx=1, pady=1)
        
        # Entry field
        self.entry = tk.Entry(
            entry_container,
            font=styles.FONTS['body'],
            bg=styles.COLORS['input_bg'],
            fg=styles.COLORS['text_primary'],
            relief=tk.FLAT,
            borderwidth=0,
            **kwargs
        )
        self.entry.pack(fill=tk.X, padx=styles.SPACING['md'], 
                       pady=styles.SPACING['sm'], ipady=6)
        
        # Placeholder
        self.placeholder = placeholder
        self.placeholder_active = False
        if placeholder:
            self._show_placeholder()
            self.entry.bind('<FocusIn>', self._hide_placeholder)
            self.entry.bind('<FocusOut>', self._show_placeholder_if_empty)
        
        # Focus ring effects
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
    
    def _on_focus_in(self, event=None):
        """Show focus ring."""
        self.focus_ring.config(bg=styles.COLORS['input_focus'])
        self._hide_placeholder()
    
    def _on_focus_out(self, event=None):
        """Hide focus ring."""
        self.focus_ring.config(bg=styles.COLORS['input_border'])
        self._show_placeholder_if_empty()
    
    def _show_placeholder(self, event=None):
        if not self.entry.get():
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=styles.COLORS['text_muted'])
            self.placeholder_active = True
    
    def _hide_placeholder(self, event=None):
        if self.placeholder_active:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=styles.COLORS['text_primary'])
            self.placeholder_active = False
    
    def _show_placeholder_if_empty(self, event=None):
        if not self.entry.get():
            self._show_placeholder()
    
    def get(self):
        if self.placeholder_active:
            return ''
        return self.entry.get()
    
    def set(self, value):
        if self.placeholder_active:
            self._hide_placeholder()
        self.entry.delete(0, tk.END)
        if value:
            self.entry.insert(0, value)
        else:
            self._show_placeholder()


class InputField(tk.Frame):
    """Alias for ModernInput for backward compatibility."""
    
    def __init__(self, parent, label='', placeholder='', icon='', **kwargs):
        super().__init__(parent, bg=styles.COLORS['bg_card'])
        
        # Use label without icon for cleaner look
        display_label = label
        
        # Label
        if display_label:
            label_widget = tk.Label(
                self,
                text=display_label,
                font=styles.FONTS['label'],
                bg=styles.COLORS['bg_card'],
                fg=styles.COLORS['text_secondary'],
                anchor=tk.W
            )
            label_widget.pack(fill=tk.X, pady=(0, styles.SPACING['xs']))
        
        # Focus ring container
        self.focus_ring = tk.Frame(self, bg=styles.COLORS['input_border'])
        self.focus_ring.pack(fill=tk.X)
        
        # Entry container
        entry_container = tk.Frame(self.focus_ring, bg=styles.COLORS['input_bg'])
        entry_container.pack(fill=tk.X, padx=1, pady=1)
        
        # Entry field
        self.entry = tk.Entry(
            entry_container,
            font=styles.FONTS['body'],
            bg=styles.COLORS['input_bg'],
            fg=styles.COLORS['text_primary'],
            relief=tk.FLAT,
            borderwidth=0,
            **kwargs
        )
        self.entry.pack(fill=tk.X, padx=styles.SPACING['md'], 
                       pady=styles.SPACING['sm'], ipady=6)
        
        # Placeholder
        self.placeholder = placeholder
        self.placeholder_active = False
        if placeholder:
            self._show_placeholder()
            self.entry.bind('<FocusIn>', self._hide_placeholder)
            self.entry.bind('<FocusOut>', self._show_placeholder_if_empty)
        
        # Focus effects
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
    
    def _on_focus_in(self, event=None):
        self.focus_ring.config(bg=styles.COLORS['input_focus'])
        self._hide_placeholder()
    
    def _on_focus_out(self, event=None):
        self.focus_ring.config(bg=styles.COLORS['input_border'])
        self._show_placeholder_if_empty()
    
    def _show_placeholder(self, event=None):
        """Show placeholder text."""
        if not self.entry.get():
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=styles.COLORS['text_muted'], font=styles.FONTS['small_italic'])
            self.placeholder_active = True
    
    def _hide_placeholder(self, event=None):
        """Hide placeholder text."""
        if self.placeholder_active:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=styles.COLORS['text_primary'], font=styles.FONTS['body'])
            self.placeholder_active = False
    
    def _show_placeholder_if_empty(self, event=None):
        """Show placeholder if field is empty."""
        if not self.entry.get():
            self._show_placeholder()
    
    def get(self):
        """Get entry value (excluding placeholder)."""
        if self.placeholder_active:
            return ''
        return self.entry.get()
    
    def set(self, value):
        """Set entry value."""
        if self.placeholder_active:
            self._hide_placeholder()
        self.entry.delete(0, tk.END)
        if value:
            self.entry.insert(0, value)
        else:
            self._show_placeholder()


class StatusBadge(tk.Label):
    """Colored status badge for build scores."""
    
    def __init__(self, parent, text='', grade='', **kwargs):
        color = styles.get_status_color(grade) if grade else styles.COLORS['text_secondary']
        
        super().__init__(
            parent,
            text=text,
            font=styles.FONTS['body_bold'],
            bg=color,
            fg=styles.COLORS['text_white'],
            padx=styles.SPACING['md'],
            pady=styles.SPACING['xs'],
            relief=tk.FLAT,
            **kwargs
        )


class StatCard(tk.Frame):
    """Modern statistics card with gradient accent."""
    
    def __init__(self, parent, icon='', title='', value='', color='primary', **kwargs):
        super().__init__(parent, bg=styles.COLORS['bg_sidebar'], **kwargs)
        
        # Accent colors
        accent_colors = {
            'primary': styles.COLORS['primary'],
            'success': styles.COLORS['success'],
            'purple': styles.COLORS['accent_purple'],
            'orange': styles.COLORS['accent_orange'],
        }
        accent = accent_colors.get(color, styles.COLORS['primary'])
        
        # Card border
        border = tk.Frame(self, bg=styles.COLORS['border'])
        border.pack(fill=tk.BOTH, expand=True)
        
        # Inner card
        inner = tk.Frame(border, bg=styles.COLORS['bg_card'])
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Left accent bar
        accent_bar = tk.Frame(inner, bg=accent, width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Content area
        content = tk.Frame(inner, bg=styles.COLORS['bg_card'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                    padx=styles.SPACING['md'], pady=styles.SPACING['md'])
        
        # Top row - icon and value
        top_row = tk.Frame(content, bg=styles.COLORS['bg_card'])
        top_row.pack(fill=tk.X)
        
        # Value (large, prominent)
        self.value_label = tk.Label(
            top_row,
            text=value,
            font=('Segoe UI', 20, 'bold'),
            bg=styles.COLORS['bg_card'],
            fg=accent,
            anchor=tk.W
        )
        self.value_label.pack(side=tk.LEFT)
        
        # Icon (right side)
        if icon:
            icon_label = tk.Label(
                top_row,
                text=icon,
                font=('Segoe UI', 18),
                bg=styles.COLORS['bg_card'],
                fg=accent,
                anchor=tk.E
            )
            icon_label.pack(side=tk.RIGHT)
        
        # Title (bottom)
        if title:
            title_label = tk.Label(
                content,
                text=title,
                font=styles.FONTS['small'],
                bg=styles.COLORS['bg_card'],
                fg=styles.COLORS['text_secondary'],
                anchor=tk.W
            )
            title_label.pack(side=tk.TOP, anchor=tk.W, pady=(styles.SPACING['xs'], 0))
    
    def update_value(self, value, color=None):
        self.value_label.config(text=value)
        if color:
            self.value_label.config(fg=color)


class InfoCard(tk.Frame):
    """Info card - alias for StatCard for compatibility."""
    
    def __init__(self, parent, icon='', title='', value='', color=None, **kwargs):
        super().__init__(parent, bg=styles.COLORS['bg_sidebar'], **kwargs)
        
        # Map old color param to new color scheme
        color_map = {
            styles.COLORS.get('text_secondary'): 'primary',
            styles.COLORS.get('info'): 'primary',
            styles.COLORS.get('primary'): 'primary',
        }
        color_key = color_map.get(color, 'primary')
        
        # Create stat card
        self.stat_card = StatCard(self, icon=icon, title=title, value=value, color=color_key)
        self.stat_card.pack(fill=tk.BOTH, expand=True)
    
    def update_value(self, value, color=None):
        self.stat_card.update_value(value, color)
    
    def update_value(self, value, color=None):
        """Update the value and optionally the color."""
        self.value_label.config(text=value)
        if color:
            self.value_label.config(fg=color)


class HeaderBar(tk.Frame):
    """Modern header bar with title and subtitle."""
    
    def __init__(self, parent, title='', subtitle='', **kwargs):
        super().__init__(
            parent,
            bg=styles.COLORS['primary'],
            height=80,
            **kwargs
        )
        
        # Prevent frame from shrinking
        self.pack_propagate(False)
        
        # Content
        content = tk.Frame(self, bg=styles.COLORS['primary'])
        content.pack(fill=tk.BOTH, expand=True, padx=styles.SPACING['xl'], pady=styles.SPACING['md'])
        
        # Title
        title_label = tk.Label(
            content,
            text=title,
            font=styles.FONTS['heading_large'],
            bg=styles.COLORS['primary'],
            fg=styles.COLORS['text_white'],
            anchor=tk.W
        )
        title_label.pack(side=tk.TOP, anchor=tk.W)
        
        # Subtitle
        if subtitle:
            subtitle_label = tk.Label(
                content,
                text=subtitle,
                font=styles.FONTS['body'],
                bg=styles.COLORS['primary'],
                fg=styles.COLORS['text_white'],
                anchor=tk.W
            )
            subtitle_label.pack(side=tk.TOP, anchor=tk.W, pady=(styles.SPACING['xs'], 0))
