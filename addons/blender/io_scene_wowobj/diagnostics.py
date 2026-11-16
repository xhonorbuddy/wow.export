"""Console output must not interrupt an import in a GUI-only Blender session."""
import builtins


def log(*args, **kwargs):
    try:
        builtins.print(*args, **kwargs)
    except (OSError, UnicodeError, ValueError):
        # Windows launchers can leave stdout detached or closed. Geometry and
        # operator error reporting must continue even when console output fails.
        pass
