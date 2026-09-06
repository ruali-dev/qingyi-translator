"""Recognize math without changing its source; render locally without a TeX install."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO

from PIL import Image


_TOKENS = re.compile(
    r"(?P<code>```[^\n]*\n.*?```|`[^`\n]+`)"
    r"|(?<!\\)(?P<block>\$\$(?P<dollars>.+?)\$\$|\\\[(?P<brackets>.+?)\\\])"
    r"|(?<!\\)\\\((?P<parens>.+?)\\\)"
    r"|(?<![\\$])\$(?![\s$])(?P<inline>[^\s$](?:[^$\n]*?[^\s$\\])?)\$(?!\d)"
    r"|(?<!\\)(?P<environment>\\begin\{(?P<env>equation\*?|align\*?|aligned|gather\*?|multline\*?|displaymath|math)\}.*?\\end\{(?P=env)\})",
    re.DOTALL,
)


@dataclass(frozen=True)
class Segment:
    raw: str
    latex: str | None = None
    display: bool = False
    protected: bool = False


def split_formulas(text: str) -> list[Segment]:
    segments: list[Segment] = []
    end = 0
    for match in _TOKENS.finditer(text):
        if match.start() > end:
            segments.append(Segment(text[end:match.start()]))
        raw = match.group()
        latex = next((match[name] for name in
                      ("dollars", "brackets", "parens", "inline", "environment")
                      if match[name] is not None), None)
        segments.append(Segment(raw, latex, bool(match["block"] or match["environment"]), True))
        end = match.end()
    if end < len(text):
        segments.append(Segment(text[end:]))
    return segments


@lru_cache(maxsize=128)
def render_formula(latex: str, display: bool, size: int) -> Image.Image | None:
    """Return an RGBA image, or None so unsupported input stays readable as source."""
    if len(latex) > 4000 or latex.count("{") > 200:
        return None
    try:
        import ziamath
        from resvg_py import svg_to_bytes

        svg = ziamath.Latex(
            latex, size=size, inline=not display, color="#182230", margin=3
        ).svg()
        # Bound raster allocation even for an unusually wide or tall expression.
        import xml.etree.ElementTree as ET
        bounds = ET.fromstring(svg).get("viewBox", "").split()
        if len(bounds) != 4 or not (0 < float(bounds[2]) <= 8000 and 0 < float(bounds[3]) <= 2000):
            return None
        png = svg_to_bytes(svg_string=svg, skip_system_fonts=True)
        with Image.open(BytesIO(png)) as image:
            return image.convert("RGBA")
    except Exception:
        # Model output is not guaranteed to be valid/supported LaTeX.
        return None
