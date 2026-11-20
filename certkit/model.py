"""奖状数据模型：CSV 解析、字段校验与中文日期。"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import List, Sequence, Tuple, Union

MAX_NAME = 20
MAX_AWARD = 40
MAX_NOTE = 60
DEFAULT_NOTE = "荣获佳绩"

NAME_HEADERS = {"姓名", "名字", "学生姓名", "学生"}
AWARD_HEADERS = {"奖项", "奖项名称", "获奖", "荣誉"}

_CN_DIGITS = "〇一二三四五六七八九"
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CertkitError(ValueError):
    """奖状数据或参数不合法。"""


@dataclass(frozen=True)
class Record:
    """一位获奖者：姓名、奖项与可选的说明。"""

    name: str
    award: str
    note: str = DEFAULT_NOTE

    def __post_init__(self) -> None:
        name = _clean(self.name)
        award = _clean(self.award)
        note = _clean(self.note) or DEFAULT_NOTE
        if not name:
            raise CertkitError("姓名不能为空")
        if not award:
            raise CertkitError("奖项不能为空")
        _check_length(name, MAX_NAME, "姓名")
        _check_length(award, MAX_AWARD, "奖项")
        _check_length(note, MAX_NOTE, "说明")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "award", award)
        object.__setattr__(self, "note", note)


def _clean(value: str) -> str:
    if not isinstance(value, str):
        raise CertkitError("字段必须是文本，当前是 %r" % (value,))
    return value.strip()


def _check_length(value: str, limit: int, label: str) -> None:
    if len(value) > limit:
        raise CertkitError(
            "%s最多 %d 个字符，当前 %d 个：%s" % (label, limit, len(value), value)
        )


def _is_header(cells: Sequence[str]) -> bool:
    if not cells or cells[0] not in NAME_HEADERS:
        return False
    return len(cells) < 2 or cells[1] in AWARD_HEADERS


def decode_bytes(data: bytes) -> str:
    """按 UTF-8（含 BOM）优先、GBK 兜底的顺序解码。"""
    if not isinstance(data, (bytes, bytearray)):
        raise CertkitError("文件内容必须是字节")
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CertkitError("无法识别文件编码，请另存为 UTF-8 或 GBK 后重试")


def parse_csv(text: str, source: str = "输入内容") -> List[Record]:
    """解析 CSV 文本；表头可选，返回有效的奖状记录。"""
    if not isinstance(text, str):
        raise CertkitError("CSV 内容必须是文本")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text))
    records: List[Record] = []
    for line_no, row in enumerate(reader, start=1):
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue
        if not records and _is_header(cells):
            continue
        if len(cells) > 3:
            raise CertkitError(
                "%s 第 %d 行有 %d 列，最多 3 列（姓名,奖项,说明）"
                % (source, line_no, len(cells))
            )
        name = cells[0] if len(cells) > 0 else ""
        award = cells[1] if len(cells) > 1 else ""
        note = cells[2] if len(cells) > 2 else ""
        if not name:
            raise CertkitError("%s 第 %d 行缺少姓名" % (source, line_no))
        if not award:
            raise CertkitError("%s 第 %d 行缺少奖项" % (source, line_no))
        try:
            records.append(
                Record(name=name, award=award, note=note or DEFAULT_NOTE)
            )
        except CertkitError as exc:
            raise CertkitError("%s 第 %d 行：%s" % (source, line_no, exc)) from exc
    if not records:
        raise CertkitError("%s 中没有有效的奖状记录" % source)
    return records


def load_records(path: Union[str, Path]) -> List[Record]:
    """读取 CSV 文件并解析；文件不存在或编码错误时抛出异常。"""
    target = Path(path)
    return parse_csv(decode_bytes(target.read_bytes()), source=str(target))


def _cn_number(value: int) -> str:
    if value < 10:
        return _CN_DIGITS[value]
    if value == 10:
        return "十"
    if value < 20:
        return "十" + _CN_DIGITS[value - 10]
    tens, ones = divmod(value, 10)
    suffix = _CN_DIGITS[ones] if ones else ""
    return _CN_DIGITS[tens] + "十" + suffix


def parse_date(value: str) -> date:
    """严格解析 YYYY-MM-DD。"""
    if not isinstance(value, str):
        raise CertkitError("日期必须是 YYYY-MM-DD 格式的文本")
    text = value.strip()
    if not _DATE_PATTERN.match(text):
        raise CertkitError("日期格式必须是 YYYY-MM-DD，例如 2026-11-21")
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise CertkitError("日期不存在：%s" % text) from exc


def format_chinese_date(value: Union[str, date]) -> str:
    """把日期格式化成「二〇二六年十一月二十一日」。"""
    if isinstance(value, str):
        day = parse_date(value)
    elif isinstance(value, date):
        day = value
    else:
        raise CertkitError("日期必须是 date 或 YYYY-MM-DD 字符串")
    year = "".join(_CN_DIGITS[int(char)] for char in "%04d" % day.year)
    return "%s年%s月%s日" % (
        year,
        _cn_number(day.month),
        _cn_number(day.day),
    )


def body_text(record: Record) -> str:
    """奖状正文，不包含标题、落款与日期。"""
    return "在「%s」中表现优异，%s。特发此证，以资鼓励。" % (
        record.award,
        record.note,
    )


def name_font_size(name: str) -> float:
    """按姓名长度选择字号，保证姓名不溢出。"""
    text = _clean(name)
    length = len(text)
    if length <= 4:
        return 16.0
    if length <= 8:
        return 13.0
    if length <= 12:
        return 10.5
    if length <= 16:
        return 8.5
    return 7.0


def wrap_text(text: str, max_width: float, font_size: float) -> List[str]:
    """按估算宽度折行，中文按一个字宽、英文按 0.55 字宽计算。"""
    if not isinstance(text, str):
        raise CertkitError("正文必须是文本")
    if max_width <= 0 or font_size <= 0:
        raise CertkitError("折行宽度和字号必须大于 0")
    lines: List[str] = []
    current = ""
    width = 0.0
    for char in text:
        char_width = font_size * (0.55 if ord(char) < 128 else 1.0)
        if current and width + char_width > max_width:
            lines.append(current)
            current = char
            width = char_width
        else:
            current += char
            width += char_width
    if current:
        lines.append(current)
    return lines


def body_lines(record: Record, max_width: float = 226.0) -> Tuple[float, List[str]]:
    """为正文选择合适字号并折行，最多三行。"""
    text = body_text(record)
    for font_size in (6.4, 6.0, 5.6, 5.2, 4.8, 4.4, 4.0, 3.6):
        lines = wrap_text(text, max_width, font_size)
        if len(lines) <= 3:
            return font_size, lines
    font_size = 3.6
    return font_size, wrap_text(text, max_width, font_size)


def format_records(records: Sequence[Record]) -> str:
    """把记录排成 CSV 文本，方便回写或调试。"""
    if not records:
        raise CertkitError("没有可输出的记录")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["姓名", "奖项", "说明"])
    for record in records:
        if not isinstance(record, Record):
            raise CertkitError("记录列表里出现了非 Record 对象")
        writer.writerow([record.name, record.award, record.note])
    return buffer.getvalue()
