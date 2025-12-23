# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Management

This project uses **uv** for Python package management.

```bash
# Sync dependencies
uv sync

# Run scripts in virtual environment
uv run python <script>

# Interactive Python session
uv run ipython
```

## build123d Architecture

**build123d** is a Python CAD library built on OpenCascade. It uses a builder pattern with context managers for constructing 3D models.

### Core Builder Pattern

```python
from build123d import *

# Create parts using BuildPart context manager
with BuildPart() as my_part:
    Box(10, 10, 5)
    # Add features with Locations
    with Locations((0, 0, 0)):
        Cylinder(2, 10, mode=Mode.SUBTRACT)  # Subtract creates holes

# Access the result via my_part.part
```

### Other Builders
- `BuildSketch` - 2D sketches for profiles
- `BuildLine` - 1D curves and paths

### Export Functions

```python
# Export to various CAD formats
export_step(part, "output.step")  # STEP format
export_stl(part, "output.stl")    # STL for 3D printing
```

### Mode Parameter

Many operations support a `mode` parameter:
- `Mode.ADD` (default) - Adds geometry
- `Mode.SUBTRACT` - Removes geometry (creates holes)
- `Mode.INTERSECT` - Intersection operation

## Resources

- [build123d Documentation](https://build123d.readthedocs.io/)
- [build123d GitHub](https://github.com/gumyr/build123d)
- [build123d Examples](https://github.com/gumyr/build123d/tree/dev/examples)
