"""
Command-line interface for the data-generator package.

Usage (once the project is installed in the active Python environment):

    generate-data --scenario tech-support --count 50 \
                  --out-dir ./sample-data/tech-support/yaml \
                  --system-description "ContosoShop SaaS" --output-format yaml

The script performs a *two-phase* argparse parse:
1.  Parse the common / bootstrap flags so we can discover the requested
    `DataGeneratorTool`.
2.  Inject the tool-specific arguments, re-parse and hand validation over
    to the tool instance.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .engine import DataGenerator
from .tool import DataGeneratorTool


def _add_common_args(p: argparse.ArgumentParser) -> None:
    """Register the arguments shared by all scenarios.

    Parameters
    ----------
    p:
        The argparse parser to which the common arguments will be added.
    """
    p.add_argument("--scenario", required=True, help="Registered scenario name.")
    p.add_argument("--count", type=int, default=1, help="Number of records.")
    p.add_argument("--out-dir", type=Path, required=True, help="Output directory.")
    p.add_argument(
        "--output-format",
        choices=["json", "yaml", "txt"],
        default="json",
        help="File format for generated records.",
    )
    # Optional Azure overrides
    p.add_argument("--azure-openai-endpoint")
    p.add_argument("--azure-openai-deployment")
    p.add_argument("--azure-openai-api-key")


def main(argv: list[str] | None = None) -> None:  # noqa: C901 (argparse flow)
    """Entry point for the `generate-data` CLI.

    This function performs a *two-phase* parsing:
    1.  Parse only the common arguments so we can discover the requested
        `DataGeneratorTool`.
    2.  After injecting scenario-specific arguments we re-parse the full
        command line and delegate validation to the tool instance.
    """
    argv = argv or sys.argv[1:]

    # ---------------- Phase-1: minimal parse --------------------------- #
    phase1 = argparse.ArgumentParser(add_help=False)
    _add_common_args(phase1)
    known, _unknown = phase1.parse_known_intermixed_args(argv)  # renamed variable

    # Retrieve the requested tool
    try:
        tool: DataGeneratorTool = DataGeneratorTool.from_name(known.scenario)
    except KeyError as exc:
        phase1.error(str(exc))
        return  # unreachable, but keeps mypy happy

    # ---------------- Phase-2: full parser ----------------------------- #
    parser = argparse.ArgumentParser(
        prog="generate-data",
        description="Synthetic data generator for Microsoft Foundry Jumpstart.",
        epilog="\n\n".join(tool.examples()),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _add_common_args(parser)

    # Inject scenario-specific args.
    for arg in tool.cli_arguments():
        flags = arg.get("flags", [])
        kwargs: dict[str, Any] = arg.get("kwargs", {})
        parser.add_argument(*flags, **kwargs)

    args = parser.parse_args(argv)

    # Validate scenario specific args
    tool.validate_args(args)

    # ---------------- Kick off generation ----------------------------- #
    gen = DataGenerator(
        tool,
        azure_openai_endpoint=args.azure_openai_endpoint,
        azure_openai_deployment=args.azure_openai_deployment,
        azure_openai_api_key=args.azure_openai_api_key,
    )
    gen.run(
        count=args.count,
        out_dir=args.out_dir,
        output_format=args.output_format,
    )


if __name__ == "__main__":
    main()
