#!/usr/bin/env python3
"""Backward-compatible launcher for :mod:`raspberry.dual_control`."""

from raspberry.dual_control import Dual_Control_System, DualControlSystem, main

__all__ = ["DualControlSystem", "Dual_Control_System", "main"]


if __name__ == "__main__":
    main()
