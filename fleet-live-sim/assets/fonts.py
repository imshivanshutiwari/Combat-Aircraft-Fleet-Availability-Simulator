"""
Font management for the Fleet Live Simulation display.

Provides cached pygame.Font instances in various sizes.
Uses system monospace fonts for a military instrument look.
"""

import pygame

# Font sizes
FONT_SIZE_TINY = 10
FONT_SIZE_SMALL = 12
FONT_SIZE_MEDIUM = 16
FONT_SIZE_LARGE = 20
FONT_SIZE_XLARGE = 28
FONT_SIZE_TITLE = 36

# Cache for initialised fonts
_font_cache = {}


def _get_font(name, size, bold=False):
    """
    Get a cached pygame font.

    Parameters
    ----------
    name : str or None
        Font family name, or None for default.
    size : int
        Font point size.
    bold : bool
        Whether to use bold variant.

    Returns
    -------
    pygame.font.Font
        The requested font.
    """
    key = (name, size, bold)
    if key not in _font_cache:
        try:
            font = pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            font = pygame.font.Font(None, size)
        _font_cache[key] = font
    return _font_cache[key]


def get_mono_font(size=FONT_SIZE_MEDIUM, bold=False):
    """Get a monospace font (for instrument displays and numbers)."""
    for name in ['consolas', 'couriernew', 'courier', 'monospace']:
        try:
            return _get_font(name, size, bold)
        except Exception:
            continue
    return _get_font(None, size, bold)


def get_sans_font(size=FONT_SIZE_MEDIUM, bold=False):
    """Get a sans-serif font (for labels and descriptions)."""
    for name in ['segoeui', 'arial', 'helvetica', 'sans']:
        try:
            return _get_font(name, size, bold)
        except Exception:
            continue
    return _get_font(None, size, bold)


def get_stencil_font(size=FONT_SIZE_LARGE):
    """Get a military stencil-style font (falls back to bold mono)."""
    for name in ['stencilstd', 'impact', 'arial black', 'arialblack']:
        try:
            return _get_font(name, size, bold=True)
        except Exception:
            continue
    return get_mono_font(size, bold=True)


def init_fonts():
    """
    Pre-initialise all commonly used fonts.

    Call this after pygame.init() and before the render loop.
    """
    if not pygame.font.get_init():
        pygame.font.init()

    # Pre-cache common sizes
    for size in [FONT_SIZE_TINY, FONT_SIZE_SMALL, FONT_SIZE_MEDIUM,
                 FONT_SIZE_LARGE, FONT_SIZE_XLARGE, FONT_SIZE_TITLE]:
        get_mono_font(size)
        get_mono_font(size, bold=True)
        get_sans_font(size)
        get_sans_font(size, bold=True)
    get_stencil_font(FONT_SIZE_TITLE)
