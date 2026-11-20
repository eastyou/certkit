"""奖状数据模型测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from certkit.model import (
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


class RecordTest(unittest.TestCase):
    def test_default_note(self) -> None:
        record = Record(name="李思远", award="三好学生")
        self.assertEqual(record.note, DEFAULT_NOTE)

    def test_strips_whitespace(self) -> None:
        record = Record(name="  李思远 ", award=" 三好学生 ", note="  ")
        self.assertEqual(record.name, "李思远")
        self.assertEqual(record.award, "三好学生")
        self.assertEqual(record.note, DEFAULT_NOTE)

    def test_rejects_empty_name(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            Record(name="  ", award="三好学生")
        self.assertIn("姓名", str(ctx.exception))

    def test_rejects_empty_award(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            Record(name="李思远", award="")
        self.assertIn("奖项", str(ctx.exception))

    def test_rejects_long_name(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            Record(name="李" * (MAX_NAME + 1), award="三好学生")
        self.assertIn(str(MAX_NAME), str(ctx.exception))

    def test_rejects_long_award(self) -> None:
        with self.assertRaises(CertkitError):
            Record(name="李思远", award="奖" * (MAX_AWARD + 1))

    def test_rejects_long_note(self) -> None:
        with self.assertRaises(CertkitError):
            Record(name="李思远", award="三好学生", note="好" * (MAX_NOTE + 1))

    def test_rejects_non_text(self) -> None:
        with self.assertRaises(CertkitError):
            Record(name=123, award="三好学生")  # type: ignore[arg-type]


class ParseCsvTest(unittest.TestCase):
    def test_without_header(self) -> None:
        records = parse_csv("李思远,三好学生,全面发展\n王雨桐,优秀干部\n")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].note, "全面发展")
        self.assertEqual(records[1].note, DEFAULT_NOTE)

    def test_with_header(self) -> None:
        records = parse_csv("姓名,奖项,说明\n李思远,三好学生,全面发展\n")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "李思远")

    def test_skips_blank_lines(self) -> None:
        records = parse_csv("\n\n李思远,三好学生\n\n\n王雨桐,优秀干部\n")
        self.assertEqual(len(records), 2)

    def test_handles_bom(self) -> None:
        records = parse_csv("\ufeff李思远,三好学生\n")
        self.assertEqual(records[0].name, "李思远")

    def test_handles_quoted_comma(self) -> None:
        records = parse_csv('李思远,三好学生,"数学、物理双科优秀"\n')
        self.assertEqual(records[0].note, "数学、物理双科优秀")

    def test_rejects_extra_columns(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            parse_csv("李思远,三好学生,全面发展,多余\n")
        self.assertIn("第 1 行", str(ctx.exception))
        self.assertIn("3 列", str(ctx.exception))

    def test_rejects_missing_name(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            parse_csv("李思远,三好学生\n,优秀干部\n")
        self.assertIn("第 2 行", str(ctx.exception))
        self.assertIn("姓名", str(ctx.exception))

    def test_rejects_missing_award(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            parse_csv("李思远,三好学生\n王雨桐\n")
        self.assertIn("奖项", str(ctx.exception))

    def test_rejects_too_long_field_with_row(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            parse_csv("李思远,三好学生\n%s,优秀干部\n" % ("王" * 21))
        self.assertIn("第 2 行", str(ctx.exception))

    def test_rejects_empty_content(self) -> None:
        for text in ("", "\n\n", "姓名,奖项,说明\n"):
            with self.assertRaises(CertkitError) as ctx:
                parse_csv(text)
            self.assertIn("没有有效", str(ctx.exception))

    def test_rejects_non_text(self) -> None:
        with self.assertRaises(CertkitError):
            parse_csv(b"abc")  # type: ignore[arg-type]


class DecodeTest(unittest.TestCase):
    def test_utf8_bom(self) -> None:
        data = "李思远,三好学生\n".encode("utf-8-sig")
        self.assertTrue(decode_bytes(data).startswith("李思远"))

    def test_gbk(self) -> None:
        data = "李思远,三好学生\n".encode("gbk")
        self.assertEqual(decode_bytes(data).strip(), "李思远,三好学生")

    def test_invalid_bytes(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            decode_bytes(b"\xff\xff\xff")
        self.assertIn("编码", str(ctx.exception))


class DateTest(unittest.TestCase):
    def test_chinese_date(self) -> None:
        cases = {
            "2026-01-01": "二〇二六年一月一日",
            "2026-10-10": "二〇二六年十月十日",
            "2026-11-21": "二〇二六年十一月二十一日",
            "2026-12-31": "二〇二六年十二月三十一日",
            "2024-02-29": "二〇二四年二月二十九日",
        }
        for value, expected in cases.items():
            self.assertEqual(format_chinese_date(value), expected)

    def test_parse_date_roundtrip(self) -> None:
        self.assertEqual(parse_date("2026-11-21").isoformat(), "2026-11-21")

    def test_rejects_bad_format(self) -> None:
        for value in ("2026/11/21", "2026-1-1", "20261121", ""):
            with self.assertRaises(CertkitError):
                parse_date(value)

    def test_rejects_missing_date(self) -> None:
        with self.assertRaises(CertkitError) as ctx:
            parse_date("2026-02-30")
        self.assertIn("不存在", str(ctx.exception))

    def test_rejects_non_text(self) -> None:
        with self.assertRaises(CertkitError):
            parse_date(20261121)  # type: ignore[arg-type]


class LayoutTest(unittest.TestCase):
    def test_name_font_size_decreases(self) -> None:
        self.assertGreater(name_font_size("李明"), name_font_size("李" * 6))
        self.assertGreater(name_font_size("李" * 6), name_font_size("李" * 10))
        self.assertGreaterEqual(name_font_size("李" * 20), 7.0)

    def test_wrap_text(self) -> None:
        self.assertEqual(wrap_text("你好世界", 20.0, 10.0), ["你好", "世界"])
        self.assertEqual(wrap_text("abc", 100.0, 10.0), ["abc"])

    def test_wrap_text_rejects_bad_params(self) -> None:
        with self.assertRaises(CertkitError):
            wrap_text("你好", 0, 10)
        with self.assertRaises(CertkitError):
            wrap_text("你好", 20, 0)

    def test_body_text(self) -> None:
        record = Record(name="李思远", award="三好学生", note="全面发展")
        self.assertEqual(
            body_text(record),
            "在「三好学生」中表现优异，全面发展。特发此证，以资鼓励。",
        )

    def test_body_lines_fit_three_lines(self) -> None:
        record = Record(
            name="李思远",
            award="奖" * MAX_AWARD,
            note="好" * MAX_NOTE,
        )
        font_size, lines = body_lines(record)
        self.assertLessEqual(len(lines), 3)
        self.assertLess(font_size, 6.4)
        self.assertEqual("".join(lines), body_text(record))


class FormatRecordsTest(unittest.TestCase):
    def test_roundtrip(self) -> None:
        records = [
            Record(name="李思远", award="三好学生", note="全面发展"),
            Record(name="王雨桐", award="优秀干部"),
        ]
        text = format_records(records)
        self.assertTrue(text.startswith("姓名,奖项,说明"))
        self.assertEqual(parse_csv(text), records)

    def test_rejects_empty(self) -> None:
        with self.assertRaises(CertkitError):
            format_records([])


class LoadRecordsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_reads_utf8_and_gbk(self) -> None:
        for encoding in ("utf-8-sig", "gbk"):
            path = self.tmp / ("名单_%s.csv" % encoding)
            path.write_bytes("李思远,三好学生\n".encode(encoding))
            records = load_records(path)
            self.assertEqual(records[0].name, "李思远")

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_records(self.tmp / "nope.csv")


if __name__ == "__main__":
    unittest.main()
