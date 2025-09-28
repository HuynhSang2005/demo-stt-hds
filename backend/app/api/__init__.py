#!/usr/bin/env python3
"""
API Package Initialization
Main API routing và version management
"""

from .v1 import router as v1_router

__all__ = ["v1_router"]
