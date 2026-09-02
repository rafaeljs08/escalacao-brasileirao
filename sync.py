#!/usr/bin/env python3
"""CLI do Brasileirão Asset Manager. Encaminha para o módulo Django."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from futebol.assetsmgr.cli import main  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(main())
