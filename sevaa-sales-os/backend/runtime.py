"""Hardened SEVAA runtime entrypoint.

Import hardened v2 first, then modular route extensions. This keeps the main
phase2 module smaller for low-token maintenance while registering all routes on
the same FastAPI app.
"""

from backend.phase2 import app
import backend.proposal_artifacts  # noqa: F401,E402 - registers artifact routes
import backend.migration_runtime  # noqa: F401,E402 - binds versioned schema init
import backend.founder_ops  # noqa: F401,E402 - registers authenticated founder ops
import backend.webhooks  # noqa: F401,E402 - registers safe inbound lead webhooks
import backend.revenue  # noqa: F401,E402 - registers founder-gated revenue/payment routes
import backend.public_enquiry  # noqa: F401,E402 - registers public quote/enquiry funnel
import backend.legacy_guard  # noqa: F401,E402 - blocks legacy v1 when auth is enabled
import backend.rate_limit  # noqa: F401,E402 - bounds v2 webhook/service request rates

__all__ = ["app"]
