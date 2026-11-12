"""Name normalization for the small-fix example."""


def normalize_name(text):
    """Lowercase and trim a name while preserving internal whitespace."""
    return text.strip().lower()
