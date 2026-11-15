"""Minimal greeter module for the first-five-minutes example."""


def greet(name):
    """Return a greeting for name."""
    cleaned = name.strip()
    return f"Hello, {cleaned}!" if cleaned else "Hello!"
