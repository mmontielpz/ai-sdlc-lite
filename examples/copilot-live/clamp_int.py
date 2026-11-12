"""Clamp integer values to an inclusive range."""


def clamp_int(value: int, lower: int, upper: int) -> int:
    """Return value limited to the inclusive range from lower to upper."""
    return min(max(value, lower), upper)
