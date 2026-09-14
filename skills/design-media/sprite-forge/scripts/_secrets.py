#!/usr/bin/env python3
"""Credential loading shared by sprite-forge provider scripts.

Copied (with attribution) from ~/.claude/skills/meshy/scripts/_provider_base.py
so sprite-forge has no cross-skill import path that breaks when either skill moves.

Lookup order: CLI override -> environment variable -> ~/.config/env/secrets.env.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SECRETS_ENV = Path.home() / ".config" / "env" / "secrets.env"


def _load_secrets_env() -> dict[str, str]:
    """Load key=value pairs from ~/.config/env/secrets.env."""
    if not _SECRETS_ENV.exists():
        return {}
    env: dict[str, str] = {}
    for line in _SECRETS_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("'\"")
    return env


def get_api_key(env_var: str, cli_override: str | None = None, required: bool = True) -> str | None:
    """Three-tier key lookup: --api-key flag, environment, secrets.env.

    With required=True (default) a missing key prints instructions and exits 1.
    With required=False it returns None so dry runs can proceed without credentials.
    """
    if cli_override:
        return cli_override
    key = os.environ.get(env_var)
    if key:
        return key
    key = _load_secrets_env().get(env_var)
    if key:
        return key
    if not required:
        return None
    print(
        f"Error: {env_var} not found.\n"
        f"Set it in one of:\n"
        f"  1. --api-key flag\n"
        f"  2. Environment variable: export {env_var}=your_key\n"
        f"  3. ~/.config/env/secrets.env: export {env_var}=your_key",
        file=sys.stderr,
    )
    sys.exit(1)
