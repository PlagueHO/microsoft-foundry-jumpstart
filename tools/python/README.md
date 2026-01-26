# Python Tools

This directory contains Python command-line tools for working with Azure AI Foundry.

## Structure

```
python/
├── src/                           # Tool source code
│   ├── create_ai_search_index/   # AI Search index creation tool
│   └── data_generator/           # Sample data generation tool
├── tests/                         # Tool tests
└── pyproject.toml                 # Python configuration
```

## Prerequisites

- Python 3.8 or later
- Azure subscription with appropriate resources

## Installation

Install tools in development mode from the `tools/python/` directory:

```bash
cd tools/python
pip install -e .[dev]
```

This installs both tools as runnable modules.

## Available Tools

### Data Generator

Generate synthetic sample data for testing AI applications.

```bash
python -m data_generator --help
python -m data_generator --output-dir ./output --count 100
```

See [src/data_generator/README.md](src/data_generator/README.md) for details.

### Create AI Search Index

Create and configure Azure AI Search indexes.

```bash
python -m create_ai_search_index --help
```

See [src/create_ai_search_index/README.md](src/create_ai_search_index/README.md) for details.

## Development

### Running Tests

```bash
cd tools/python
pytest tests/ -v
```

### Linting

```bash
ruff check src/
```

### Type Checking

```bash
mypy src/
```

### Code Formatting

```bash
ruff format src/
```

## Adding New Tools

1. Create a new directory under `src/` with this structure:
   ```
   src/my_new_tool/
   ├── __init__.py
   ├── __main__.py      # Entry point for python -m my_new_tool
   ├── cli.py           # CLI argument parsing
   └── engine.py        # Business logic
   ```

2. Add tests under `tests/my_new_tool/`

3. Update this README with tool documentation

## Learn More

- [Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
