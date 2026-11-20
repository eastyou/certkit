"""把奖状渲染成可打印的 A4 横向 SVG 与 HTML。"""

from __future__ import annotations

import html
from typing import List, Sequence

from .model import (
    CertkitError,
    Record,
    body_lines,
    name_font_size,
)

PAGE_WIDTH_MM = 297.0
PAGE_HEIGHT_MM = 210.0

RED = "#b91c1c"
STAMP_RED = "#dc2626"
GOLD = "#b45309"
INK = "#0f172a"


def _num(value: float) -> str:
    text = "%.3f" % value
    return text.rstrip("0").rstrip(".") if "." in text else text


def _validate_head(title: str, issuer: str, date_text: str) -> None:
    if not isinstance(title, str) or not title.strip():
        raise CertkitError("标题不能为空")
    if not isinstance(issuer, str) or not issuer.strip():
        raise CertkitError("颁发单位不能为空")
    if not isinstance(date_text, str) or not date_text.strip():
        raise CertkitError("日期不能为空")


def render_svg(
    record: Record,
    title: str = "奖状",
    issuer: str = "学校",
    date_text: str = "二〇二六年十一月二十一日",
) -> str:
    """生成一张 A4 横向奖状。"""
    if not isinstance(record, Record):
        raise CertkitError("record 必须是 Record 实例")
    _validate_head(title, issuer, date_text)

    center_x = PAGE_WIDTH_MM / 2
    name_size = name_font_size(record.name)
    body_size, lines = body_lines(record)

    parts: List[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" '
        'viewBox="0 0 %s %s">'
        % (
            _num(PAGE_WIDTH_MM),
            _num(PAGE_HEIGHT_MM),
            _num(PAGE_WIDTH_MM),
            _num(PAGE_HEIGHT_MM),
        ),
        '<rect width="%s" height="%s" fill="#fffdfa"/>'
        % (_num(PAGE_WIDTH_MM), _num(PAGE_HEIGHT_MM)),
        '<rect x="10" y="10" width="277" height="190" fill="none" '
        'stroke="%s" stroke-width="1.5"/>' % RED,
        '<rect x="14" y="14" width="269" height="182" fill="none" '
        'stroke="%s" stroke-width="0.5"/>' % RED,
    ]

    for x, y in ((10, 10), (287, 10), (10, 200), (287, 200)):
        parts.append(
            '<polygon points="%s,%s %s,%s %s,%s %s,%s" fill="%s"/>'
            % (
                _num(x),
                _num(y - 4),
                _num(x + 4),
                _num(y),
                _num(x),
                _num(y + 4),
                _num(x - 4),
                _num(y),
                GOLD,
            )
        )

    parts.extend(
        [
            '<text x="%s" y="57" font-size="21" font-weight="700" '
            'letter-spacing="10" text-anchor="middle" fill="%s">%s</text>'
            % (_num(center_x), RED, html.escape(title.strip())),
            '<text x="%s" y="67" font-size="4.2" letter-spacing="3" '
            'text-anchor="middle" fill="%s">CERTIFICATE OF ACHIEVEMENT</text>'
            % (_num(center_x), GOLD),
            '<line x1="%s" y1="75" x2="%s" y2="75" stroke="%s" '
            'stroke-width="0.4"/>'
            % (_num(center_x - 55), _num(center_x + 55), GOLD),
            '<text x="%s" y="101" font-size="%s" font-weight="700" '
            'text-anchor="middle" fill="%s">%s</text>'
            % (
                _num(center_x),
                _num(name_size),
                INK,
                html.escape(record.name),
            ),
            '<line x1="%s" y1="109" x2="%s" y2="109" stroke="#e2e8f0" '
            'stroke-width="0.6"/>'
            % (_num(center_x - 70), _num(center_x + 70)),
        ]
    )

    base_y = 130.0
    gap = body_size * 1.9
    start_y = base_y - (len(lines) - 1) * gap / 2
    for offset, line in enumerate(lines):
        parts.append(
            '<text x="%s" y="%s" font-size="%s" letter-spacing="0.6" '
            'text-anchor="middle" fill="#334155">%s</text>'
            % (
                _num(center_x),
                _num(start_y + offset * gap),
                _num(body_size),
                html.escape(line),
            )
        )

    parts.extend(
        [
            '<g transform="rotate(-8 %s %s)">' % (_num(214), _num(166)),
            '<circle cx="214" cy="166" r="15" fill="none" stroke="%s" '
            'stroke-width="1.1"/>' % STAMP_RED,
            '<circle cx="214" cy="166" r="12" fill="none" stroke="%s" '
            'stroke-width="0.35"/>' % STAMP_RED,
            '<text x="214" y="172.5" font-size="11" font-weight="700" '
            'text-anchor="middle" fill="%s" opacity="0.85">奖</text>'
            % STAMP_RED,
            "</g>",
            '<text x="262" y="173" font-size="5.2" text-anchor="end" '
            'fill="#334155">%s</text>' % html.escape(issuer.strip()),
            '<text x="262" y="183" font-size="5.2" text-anchor="end" '
            'fill="#334155">%s</text>' % html.escape(date_text.strip()),
            '<text x="20" y="197" font-size="2.6" fill="#94a3b8">'
            "certkit · A4 横向 · 沿边框裁剪即可</text>",
        ]
    )

    parts.append("</svg>")
    return "\n".join(parts)


STYLE = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 8mm 0 12mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .toolbar {
    width: 297mm;
    margin: 0 auto 6mm;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 13px;
  }
  .toolbar strong { font-size: 15px; letter-spacing: 1px; }
  .toolbar span { color: #64748b; font-size: 12px; }
  .sheet {
    width: 297mm;
    height: 210mm;
    margin: 0 auto 8mm;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    overflow: hidden;
    page-break-after: always;
    break-after: page;
  }
  .sheet:last-child { page-break-after: auto; break-after: auto; }
  .sheet svg { display: block; }
  @page { size: A4 landscape; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""


def render_html(
    records: Sequence[Record],
    title: str = "奖状",
    issuer: str = "学校",
    date_text: str = "二〇二六年十一月二十一日",
) -> str:
    """生成完整 HTML，每页一张奖状。"""
    if not isinstance(records, (list, tuple)):
        raise CertkitError("records 必须是奖状记录列表")
    if not records:
        raise CertkitError("没有可生成的奖状记录")
    _validate_head(title, issuer, date_text)
    for record in records:
        if not isinstance(record, Record):
            raise CertkitError("记录列表里出现了非 Record 对象")

    sheets: List[str] = []
    for record in records:
        sheets.append(
            '<section class="sheet">%s</section>'
            % render_svg(
                record,
                title=title,
                issuer=issuer,
                date_text=date_text,
            )
        )

    toolbar = (
        '<div class="toolbar"><strong>%s</strong>'
        "<span>共 %d 张 · %s · %s</span></div>"
        % (
            html.escape(title.strip()),
            len(records),
            html.escape(issuer.strip()),
            html.escape(date_text.strip()),
        )
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n%s\n</body>\n</html>\n"
        % (
            html.escape(title.strip()),
            STYLE,
            toolbar,
            "\n".join(sheets),
        )
    )
