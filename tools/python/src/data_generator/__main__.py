"""
`python -m data_generator ...` entry-point.

Allows running the generator without installing the package first, provided
the repo's `src` folder is on PYTHONPATH.
"""
from .cli import main

if __name__ == "__main__":
    main()
