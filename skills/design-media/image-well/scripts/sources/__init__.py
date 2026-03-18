"""Image source registry and presets."""

from .base import ImageSource

# Lazy imports to avoid loading all sources at startup
_SOURCE_MODULES: dict[str, tuple[str, str]] = {
    # name -> (module_name, class_name)
    "openverse": ("openverse", "OpenverseSource"),
    "wikimedia": ("wikimedia", "WikimediaSource"),
    "met": ("met_museum", "MetMuseumSource"),
    "nasa": ("nasa", "NasaSource"),
    "pexels": ("pexels", "PexelsSource"),
    "pixabay": ("pixabay", "PixabaySource"),
    "rijksmuseum": ("rijksmuseum", "RijksmuseumSource"),
    "unsplash": ("unsplash", "UnsplashSource"),
    "smithsonian": ("smithsonian", "SmithsonianSource"),
    "europeana": ("europeana", "EuropeanaSource"),
    "iconify": ("iconify", "IconifySource"),
    "pollinations": ("pollinations", "PollinationsSource"),
}

PRESETS: dict[str, dict] = {
    "military": {"sources": ["nasa", "wikimedia", "smithsonian"], "license": "cc0"},
    "museum": {"sources": ["met", "rijksmuseum", "smithsonian"], "license": "cc0"},
    "texture": {"sources": ["wikimedia", "pollinations"], "license": "any"},
    "stock": {"sources": ["pexels", "pixabay", "unsplash"], "license": "any"},
    "all-free": {"sources": ["openverse", "wikimedia", "met", "nasa", "smithsonian"], "license": "any"},
}

TIER_1 = ["openverse", "wikimedia", "met", "nasa"]
TIER_2 = ["pexels", "pixabay", "rijksmuseum", "unsplash"]
TIER_3 = ["smithsonian", "europeana", "iconify", "pollinations"]


def get_source(name: str) -> ImageSource | None:
    """Instantiate a source by name. Returns None if module not found."""
    if name not in _SOURCE_MODULES:
        return None
    module_name, class_name = _SOURCE_MODULES[name]
    try:
        import importlib
        mod = importlib.import_module(f".{module_name}", package="sources")
        cls = getattr(mod, class_name)
        return cls()
    except (ImportError, AttributeError) as e:
        import sys
        print(f"  \u26a0 Failed to load source '{name}': {e}", file=sys.stderr)
        return None


def list_sources() -> list[str]:
    """Return all registered source names."""
    return list(_SOURCE_MODULES.keys())


def get_all_sources() -> list[ImageSource]:
    """Instantiate all available sources."""
    sources = []
    for name in _SOURCE_MODULES:
        src = get_source(name)
        if src is not None:
            sources.append(src)
    return sources
