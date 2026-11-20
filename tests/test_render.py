"""奖状渲染测试。"""

from __future__ import annotations

import unittest

from certkit.model import CertkitError, Record, name_font_size
from certkit.render import RED, STAMP_RED, render_html, render_svg

DATE = "二〇二六年十一月二十一日"


def sample() -> Record:
    return Record(name="李思远", award="三好学生", note="德智体美劳全面发展")


class RenderSvgTest(unittest.TestCase):
    def test_page_size(self) -> None:
        svg = render_svg(sample(), issuer="星海中学", date_text=DATE)
        self.assertIn('width="297mm"', svg)
        self.assertIn('height="210mm"', svg)

    def test_contains_fields(self) -> None:
        svg = render_svg(sample(), title="荣誉证书", issuer="星海中学", date_text=DATE)
        self.assertIn("荣誉证书", svg)
        self.assertIn("李思远", svg)
        self.assertIn("三好学生", svg)
        self.assertIn("德智体美劳全面发展", svg)
        self.assertIn("特发此证，以资鼓励。", svg)
        self.assertIn("星海中学", svg)
        self.assertIn(DATE, svg)

    def test_border_and_stamp(self) -> None:
        svg = render_svg(sample())
        self.assertGreaterEqual(svg.count(RED), 3)
        self.assertIn(STAMP_RED, svg)
        self.assertIn(">奖</text>", svg)
        self.assertEqual(svg.count("<rect"), 3)

    def test_escapes_text(self) -> None:
        record = Record(name="<李明>", award="A&B")
        svg = render_svg(record, title="<奖状>", issuer="<学校>")
        self.assertIn("&lt;李明&gt;", svg)
        self.assertIn("A&amp;B", svg)
        self.assertIn("&lt;奖状&gt;", svg)
        self.assertNotIn("<李明>", svg)

    def test_long_name_uses_smaller_font(self) -> None:
        short = render_svg(Record(name="李明", award="三好学生"))
        long = render_svg(Record(name="李" * 18, award="三好学生"))
        short_size = 'font-size="%s"' % int(name_font_size("李明"))
        long_size = 'font-size="7"'
        self.assertIn(short_size, short)
        self.assertIn(long_size, long)

    def test_rejects_bad_head(self) -> None:
        with self.assertRaises(CertkitError):
            render_svg(sample(), title=" ")
        with self.assertRaises(CertkitError):
            render_svg(sample(), issuer="")
        with self.assertRaises(CertkitError):
            render_svg(sample(), date_text="")

    def test_rejects_non_record(self) -> None:
        with self.assertRaises(CertkitError):
            render_svg("李思远")  # type: ignore[arg-type]


class RenderHtmlTest(unittest.TestCase):
    def test_one_sheet_per_record(self) -> None:
        records = [
            Record(name="李思远", award="三好学生"),
            Record(name="王雨桐", award="优秀干部"),
            Record(name="陈子墨", award="学习进步奖"),
        ]
        page = render_html(records, issuer="星海中学", date_text=DATE)
        self.assertEqual(page.count('class="sheet"'), 3)
        self.assertIn("共 3 张", page)
        self.assertIn("星海中学", page)
        self.assertIn(DATE, page)

    def test_landscape_print_css(self) -> None:
        page = render_html([sample()], date_text=DATE)
        self.assertIn("A4 landscape", page)
        self.assertIn("@media print", page)
        self.assertIn('lang="zh-CN"', page)

    def test_title_is_escaped(self) -> None:
        page = render_html([sample()], title="<奖状>", date_text=DATE)
        self.assertIn("<title>&lt;奖状&gt;</title>", page)

    def test_rejects_empty_records(self) -> None:
        with self.assertRaises(CertkitError):
            render_html([])

    def test_rejects_non_sequence(self) -> None:
        with self.assertRaises(CertkitError):
            render_html(sample())  # type: ignore[arg-type]

    def test_rejects_non_record_items(self) -> None:
        with self.assertRaises(CertkitError):
            render_html([sample(), "王雨桐"])  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
