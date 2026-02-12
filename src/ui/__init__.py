"""
UI Package for Bin-Xray
Modern UI components and styling
"""

from .styles import COLORS, FONTS, SPACING, ICONS, BUTTON_STYLES
from .components import (
    ModernButton,
    Card,
    FloatingCard,
    InputField,
    ModernInput,
    StatusBadge,
    InfoCard,
    StatCard,
    HeaderBar,
    SectionHeader,
    SectionBadge
)
from .main_window import ModernMainWindow

__all__ = [
    'COLORS',
    'FONTS', 
    'SPACING',
    'ICONS',
    'BUTTON_STYLES',
    'ModernButton',
    'Card',
    'FloatingCard',
    'InputField',
    'ModernInput',
    'StatusBadge',
    'InfoCard',
    'StatCard',
    'HeaderBar',
    'SectionHeader',
    'SectionBadge',
    'ModernMainWindow',
]
