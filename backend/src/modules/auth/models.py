"""Auth has no dedicated SQL models.

Users live in :mod:`src.modules.users.models`; refresh tokens and the access
token blacklist are stored in Redis (see :mod:`src.modules.auth.service`).
This module exists to satisfy the canonical module layout.
"""

from __future__ import annotations
