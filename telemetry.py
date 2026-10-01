"""Backward-compatible launcher for :mod:`pc.telemetry`."""

from pc.telemetry import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
