"""LilRAE's intentionally narrow pre-backend command surface."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from lilrae import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the metadata-only command parser."""
    parser = argparse.ArgumentParser(
        prog="lilrae",
        description="Inspect the installed LilRAE distribution.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Run the metadata-only command."""
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()


if __name__ == "__main__":
    main()
