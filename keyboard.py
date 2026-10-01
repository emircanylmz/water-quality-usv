"""Backward-compatible launcher for :mod:`pc.keyboard`."""

from pc.keyboard import main, monitor_serial

__all__ = ["main", "monitor_serial"]


if __name__ == "__main__":
    main()
