# File Name: _font.py
# Description: Cross-platform Unicode TTF resolver for tests (Windows, Linux CI, matplotlib fallback).
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import os

_CANDIDATES = (
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)


def _resolve() -> str:
    for p in _CANDIDATES:
        if os.path.exists(p):
            return p
    try:  # matplotlib bundles DejaVuSans (Vietnamese-capable)
        import matplotlib

        p = os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf")
        if os.path.exists(p):
            return p
    except ImportError:
        pass
    return _CANDIDATES[0]


FONT = _resolve()
