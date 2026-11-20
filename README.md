# certkit

[![CI](https://github.com/eastyou/certkit/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/certkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给老师用的奖状生成器：用 Excel 维护一份名单，一条命令生成整套 A4 横向奖状，每页一张，直接打印。**零依赖，不联网，矢量排版。**

姓名太长时间会自动缩小字号，正文过长会自动折行，红色印章、双线边框和中文落款日期都是现成的。

## 特性

- **一行一人**：CSV 三列 `姓名,奖项,说明`，说明可省略，默认「荣获佳绩」
- **表头可选**：带不带 `姓名,奖项,说明` 表头都能识别
- **编码兼容**：UTF-8（含 BOM）与 GBK 自动识别，Excel 另存的 CSV 可直接用
- **逐行校验**：空姓名、空奖项、多余列、字段超长都会指出具体行号
- **A4 横向**：297×210mm，双线红框、四角金饰、红色「奖」印章
- **自适应排版**：姓名按长度选字号，正文自动折行，最多三行
- **中文日期**：`--date 2026-11-21` 自动写成「二〇二六年十一月二十一日」
- **58 个单元测试**：覆盖 CSV 解析、编码识别、字段边界、日期格式化、渲染与命令行

## 安装

```bash
pip install certkit
```

也可以直接下载源码，在项目目录里运行：

```bash
python -m certkit --help
```

## 用法

准备名单 `获奖名单.csv`：

```csv
姓名,奖项,说明
李思远,三好学生,德智体美劳全面发展
王雨桐,优秀学生干部,热心服务班级
陈子墨,学习进步奖
```

生成奖状：

```bash
certkit -i 获奖名单.csv --issuer 星海中学 --date 2026-11-21 -o 奖状.html
```

自定义标题：

```bash
certkit -i 获奖名单.csv --title 荣誉证书 -o 荣誉证书.html
```

打开 HTML 后按 `Ctrl/Cmd + P`，纸张选 **A4 横向**、边距选「无」、勾选「背景图形」即可打印。每页一张，沿边框裁剪。

## 名单格式

| 列 | 是否必填 | 长度上限 | 说明 |
| --- | --- | --- | --- |
| 姓名 | 必填 | 20 字 | 显示在奖状中央，字号自适应 |
| 奖项 | 必填 | 40 字 | 填入正文的「」中 |
| 说明 | 可选 | 60 字 | 默认「荣获佳绩」 |

正文固定为：

> 在「奖项」中表现优异，说明。特发此证，以资鼓励。

## 命令行参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `-i, --input` | 必填 | 名单 CSV 路径 |
| `-o, --output` | `奖状.html` | 输出 HTML 路径 |
| `--title` | `奖状` | 奖状大标题 |
| `--issuer` | `学校` | 颁发单位，显示在右下角 |
| `--date` | 今天 | 颁发日期，格式 `YYYY-MM-DD` |

## 工作原理

1. **读取**：按 UTF-8（含 BOM）→ GBK 的顺序解码，识别可选表头。
2. **校验**：逐行检查列数、姓名、奖项与长度，错误信息带行号。
3. **排版**：每张奖状是一页 297×210mm 的 SVG，标题、姓名、正文、落款、印章分层绘制。
4. **打印**：HTML 内置 `@page { size: A4 landscape }`，浏览器直接按横向输出。

核心接口：

```python
from certkit import Record, format_chinese_date, parse_csv, render_html

records = parse_csv("姓名,奖项\n李思远,三好学生\n")
page = render_html(records, issuer="星海中学", date_text=format_chinese_date("2026-11-21"))
```

## 项目结构

```
certkit/
├── certkit/
│   ├── model.py    # CSV 解析、字段校验、中文日期
│   ├── render.py   # A4 横向 SVG 与 HTML 排版
│   └── cli.py      # 命令行入口
├── examples/       # 示例名单
├── tests/          # 58 个单元测试
└── pyproject.toml
```

## 开发

```bash
python -m unittest discover -s tests -v
python -m certkit -i examples/获奖名单.csv --date 2026-11-21 -o 奖状.html
```

## 许可证

[MIT](LICENSE) © 2026 eastyou
