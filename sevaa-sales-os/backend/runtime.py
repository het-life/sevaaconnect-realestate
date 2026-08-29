"""Hardened SEVAA runtime entrypoint.

Import hardened v2 first, then modular route extensions. This keeps the main
phase2 module smaller for low-token maintenance while registering all routes on
the same FastAPI app.
"""

from backend.phase2 import app
import backend.proposal_artifacts  # noqa: F401,E402 - registers artifact routes

__all__ = ["app"]
