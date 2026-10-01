"""Backward-compatible launcher for the historical misspelled command."""

from pc.xlsx_logger import build_parser, main, run_logger

__all__ = ["build_parser", "main", "run_logger"]


if __name__ == "__main__":
    main()
