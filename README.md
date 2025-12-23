# build123d Playground

A workspace for experimenting with [build123d](https://github.com/gumyr/build123d), a Python CAD library.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

### Requirements

- Python 3.12+
- uv

### Installation

All dependencies are already installed. To verify:

```bash
uv run python -c "import build123d; print(build123d.__version__)"
```

## Usage

### Running Examples

Run the example script:

```bash
uv run python example.py
```

This creates a box with a cylindrical hole and exports it as `box_with_hole.step`.

### Running Scripts

Use `uv run` to execute Python scripts in the virtual environment:

```bash
uv run python your_script.py
```

### Interactive Session

Start an IPython session with build123d:

```bash
uv run ipython
```

Then in IPython:

```python
from build123d import *

# Create shapes interactively
with BuildPart() as part:
    Box(10, 10, 10)
```

## Project Structure

```
build123d-playground/
├── .venv/              # Virtual environment (managed by uv)
├── .python-version     # Python version specification
├── pyproject.toml      # Project configuration and dependencies
├── uv.lock            # Dependency lock file
├── example.py         # Example CAD model
└── README.md          # This file
```

## Dependencies

- build123d: CAD modeling library
- IPython: Interactive Python shell (included with build123d)
- vtk: 3D visualization
- And other dependencies required by build123d

## Resources

- [build123d Documentation](https://build123d.readthedocs.io/)
- [build123d GitHub](https://github.com/gumyr/build123d)
- [build123d Examples](https://github.com/gumyr/build123d/tree/dev/examples)
