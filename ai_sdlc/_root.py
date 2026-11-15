"""Locate the AI-SDLC Lite framework root from a source checkout or installed wheel."""

from pathlib import Path


def framework_root():
    """Return the source checkout root, or the bundled _framework data directory when installed."""
    package_dir = Path(__file__).resolve().parent
    checkout = package_dir.parent
    if (checkout / 'scripts' / 'verify_scope.py').is_file():
        return checkout
    bundled = package_dir / '_framework'
    if (bundled / 'scripts' / 'verify_scope.py').is_file():
        return bundled
    return checkout
