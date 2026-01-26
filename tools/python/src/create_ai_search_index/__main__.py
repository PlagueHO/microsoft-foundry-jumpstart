"""
`python -m create_ai_search_index ...` entry-point.

Allows running the index pipeline builder without installing the package first,
provided the repo's `src` folder is on PYTHONPATH.
"""
from .cli import main

if __name__ == "__main__":
    main()
