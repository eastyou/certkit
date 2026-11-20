"""命令行入口：从 CSV 生成可打印的奖状。"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Optional, Sequence

from .model import (
    CertkitError,
    load_records,
    format_chinese_date,
    parse_date,
)
from .render import render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="certkit",
        description="奖状生成器：读取 CSV 名单，生成 A4 横向可打印奖状",
    )
    parser.add_argument("--version", action="version", version="certkit 0.1.0")
    parser.add_argument(
        "-i", "--input", required=True, help="名单 CSV，列为 姓名,奖项,说明"
    )
    parser.add_argument("-o", "--output", default="奖状.html", help="输出 HTML 路径")
    parser.add_argument("--title", default="奖状", help="奖状标题，默认「奖状」")
    parser.add_argument("--issuer", default="学校", help="颁发单位，默认「学校」")
    parser.add_argument(
        "--date", default=None, help="颁发日期 YYYY-MM-DD，默认今天"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        records = load_records(args.input)
        chosen = parse_date(args.date) if args.date else date.today()
        date_text = format_chinese_date(chosen)
        page = render_html(
            records,
            title=args.title,
            issuer=args.issuer,
            date_text=date_text,
        )
    except CertkitError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取名单失败: %s" % exc, file=sys.stderr)
        return 1

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    print("已生成 %s：%d 张奖状，%s" % (args.output, len(records), date_text))
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 横向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
