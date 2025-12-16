#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
县级访谈文本汇总工具

功能：
- 递归读取某个县目录下的 docx / txt 访谈提纲与文本
- 提取纯文本后按文件名顺序合并，生成单一汇总文件
- 默认输出到 output/2_merged_texts/{县目录名}_combined.txt

用法示例：
    python county_text_merger.py --county-dir input_text/0714-0715河北省平乡县/0714-0715河北省平乡县文本
    python county_text_merger.py --county-dir input_text/0806独山县 --output /tmp/独山县汇总.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from docx import Document


SUPPORTED_SUFFIXES = {".docx", ".txt"}
DEFAULT_OUTPUT_ROOT = Path(__file__).parent / "output" / "2_merged_texts"


def read_docx(file_path: Path) -> str:
    """提取 docx 文本内容，去掉空段落。"""
    doc = Document(str(file_path))
    parts: List[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def read_txt(file_path: Path) -> str:
    """读取 txt 文本内容。"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def collect_files(root_dir: Path) -> List[Path]:
    """递归收集支持的文件，按文件名排序。"""
    return sorted(
        [p for p in root_dir.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES],
        key=lambda p: p.name,
    )


def merge_county_texts(county_dir: Path, output_file: Path) -> None:
    files = collect_files(county_dir)
    if not files:
        raise FileNotFoundError(f"未在目录中找到 docx / txt 文件: {county_dir}")

    sections: List[str] = []
    skipped: List[str] = []

    for file_path in files:
        try:
            if file_path.suffix.lower() == ".docx":
                content = read_docx(file_path)
            else:
                content = read_txt(file_path)
        except Exception as exc:  # pylint: disable=broad-except
            skipped.append(f"{file_path.name}（读取失败：{exc}）")
            continue

        if not content:
            skipped.append(f"{file_path.name}（内容为空）")
            continue

        header = f"===== {file_path.name} ====="
        sections.append(f"{header}\n{content.strip()}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(sections))

    print(f"✅ 已合并 {len(sections)} 个文件 → {output_file}")
    if skipped:
        print(f"⚠️  跳过 {len(skipped)} 个文件：")
        for info in skipped:
            print(f"   - {info}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="县级访谈文本汇总合并工具")
    parser.add_argument(
        "--county-dir",
        required=True,
        help="指定某个县的目录路径，内部包含 docx / txt（支持递归）",
    )
    parser.add_argument(
        "--output",
        help="自定义输出文件路径；默认输出到 output/2_merged_texts/{县目录名}_combined.txt",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    county_dir = Path(args.county_dir).expanduser().resolve()
    if not county_dir.exists():
        raise FileNotFoundError(f"目录不存在：{county_dir}")

    county_name = county_dir.name
    output_file = (
        Path(args.output).expanduser().resolve()
        if args.output
        else (DEFAULT_OUTPUT_ROOT / f"{county_name}_combined.txt")
    )

    merge_county_texts(county_dir, output_file)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"❌ 处理失败：{exc}", file=sys.stderr)
        sys.exit(1)

