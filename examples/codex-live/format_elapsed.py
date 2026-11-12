"""Format nonnegative integer seconds for elapsed-time display."""


def format_elapsed(seconds: int) -> str:
    """Return M:SS, allowing minutes to grow without an upper bound."""
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}:{remainder:02d}"
