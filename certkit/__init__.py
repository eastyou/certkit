"""certkit：A4 横向奖状生成器。"""

from __future__ import annotations

from .model import (
    DEFAULT_NOTE,
    MAX_AWARD,
    MAX_NAME,
    MAX_NOTE,
    CertkitError,
    Record,
    body_lines,
    body_text,
    decode_bytes,
    format_chinese_date,
    format_records,
    load_records,
    name_font_size,
    parse_csv,
    parse_date,
    wrap_text,
)
from .render import render_html, render_svg

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_NOTE",
    "MAX_AWARD",
    "MAX_NAME",
    "MAX_NOTE",
    "CertkitError",
    "Record",
    "body_lines",
    "body_text",
    "decode_bytes",
    "format_chinese_date",
    "format_records",
    "load_records",
    "name_font_size",
    "parse_csv",
    "parse_date",
    "render_html",
    "render_svg",
    "wrap_text",
    "__version__",
]
