"""奖状命令行入口测试。"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import List, Tuple

from certkit.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.csv = self.tmp / "名单.csv"
        self.csv.write_text(
            "姓名,奖项,说明\n李思远,三好学生,全面发展\n王雨桐,优秀干部\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, argv: List[str]) -> Tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_generate(self) -> None:
        output = self.tmp / "c.html"
        code, out, err = self.run_cli(
            ["-i", str(self.csv), "-o", str(output), "--date", "2026-11-21"]
        )
        self.assertEqual(code, 0, err)
        self.assertTrue(output.exists())
        self.assertIn("2 张奖状", out)
        self.assertIn("二〇二六年十一月二十一日", out)
        page = output.read_text(encoding="utf-8")
        self.assertEqual(page.count('class="sheet"'), 2)
        self.assertIn("李思远", page)

    def test_custom_issuer_and_title(self) -> None:
        output = self.tmp / "c.html"
        code, _, err = self.run_cli(
            [
                "-i",
                str(self.csv),
                "-o",
                str(output),
                "--issuer",
                "星海中学",
                "--title",
                "荣誉证书",
                "--date",
                "2026-11-21",
            ]
        )
        self.assertEqual(code, 0, err)
        page = output.read_text(encoding="utf-8")
        self.assertIn("星海中学", page)
        self.assertIn("荣誉证书", page)

    def test_default_date_is_today(self) -> None:
        output = self.tmp / "c.html"
        code, out, err = self.run_cli(["-i", str(self.csv), "-o", str(output)])
        self.assertEqual(code, 0, err)
        self.assertIn("年", out)
        self.assertIn("月", out)

    def test_missing_input_file(self) -> None:
        code, _, err = self.run_cli(["-i", str(self.tmp / "nope.csv")])
        self.assertEqual(code, 1)
        self.assertIn("读取名单失败", err)

    def test_invalid_date(self) -> None:
        code, _, err = self.run_cli(
            ["-i", str(self.csv), "--date", "2026-13-01"]
        )
        self.assertEqual(code, 2)
        self.assertIn("日期", err)

    def test_invalid_csv(self) -> None:
        bad = self.tmp / "bad.csv"
        bad.write_text("李思远,三好学生,说明,多余\n", encoding="utf-8")
        code, _, err = self.run_cli(["-i", str(bad)])
        self.assertEqual(code, 2)
        self.assertIn("3 列", err)

    def test_missing_input_argument(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli([])
        self.assertEqual(ctx.exception.code, 2)

    def test_write_failure(self) -> None:
        output = self.tmp / "missing" / "c.html"
        code, _, err = self.run_cli(
            ["-i", str(self.csv), "-o", str(output), "--date", "2026-11-21"]
        )
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_output_is_reproducible(self) -> None:
        first = self.tmp / "a.html"
        second = self.tmp / "b.html"
        for path in (first, second):
            code, _, err = self.run_cli(
                ["-i", str(self.csv), "-o", str(path), "--date", "2026-11-21"]
            )
            self.assertEqual(code, 0, err)
        self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
