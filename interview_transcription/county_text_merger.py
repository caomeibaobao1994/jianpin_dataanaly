#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
县级访谈文本汇总工具

功能：
- 读取县目录下的基础信息.txt
- 递归读取访谈文本目录下的 docx / txt 文件
- 读取县目录下的案例文件（.docx格式）
- 按照【基础信息】【访谈记录】【案例补充】格式组织合并
- 默认输出到 output/2_merged_texts/{县目录名}_combined.txt

用法示例：
    python county_text_merger.py --county-dir input_text/0714-0715河北省平乡县
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


def read_basic_info(county_dir: Path) -> str:
    """读取县域基础信息"""
    info_file = county_dir / "基础信息.txt"
    if info_file.exists():
        try:
            content = read_txt(info_file)
            print(f"✓ 读取基础信息: {info_file.name} ({len(content)} 字符)")
            return content
        except Exception as e:
            print(f"⚠️  读取基础信息失败: {e}")
    else:
        print(f"⚠️  未找到基础信息文件")
    return ""


def collect_interview_files(county_dir: Path) -> List[Path]:
    """收集访谈文本文件（在"文本"子目录中）"""
    interview_files = []
    for subdir in county_dir.iterdir():
        if subdir.is_dir() and "文本" in subdir.name:
            files = sorted(
                [p for p in subdir.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES],
                key=lambda p: p.name,
            )
            interview_files.extend(files)
    return interview_files


def collect_case_files(county_dir: Path) -> List[Path]:
    """收集案例文件（县目录根目录下的.docx，排除文本子目录）"""
    case_files = []
    for file_path in county_dir.glob("*.docx"):
        # 排除临时文件和基础信息文件
        if not file_path.name.startswith("~") and file_path.name != "基础信息.txt":
            case_files.append(file_path)
    return sorted(case_files, key=lambda p: p.name)


def merge_county_texts(county_dir: Path, output_file: Path) -> None:
    """合并县域的基础信息、访谈文本、案例文件"""
    
    # 1. 读取基础信息
    print("\n" + "="*60)
    print("步骤1: 读取基础信息")
    print("="*60)
    basic_info = read_basic_info(county_dir)
    
    # 2. 读取访谈文本
    print("\n" + "="*60)
    print("步骤2: 读取访谈文本")
    print("="*60)
    interview_files = collect_interview_files(county_dir)
    if not interview_files:
        print("⚠️  未找到访谈文本文件")
    
    interview_sections: List[str] = []
    interview_skipped: List[str] = []
    
    for file_path in interview_files:
        try:
            if file_path.suffix.lower() == ".docx":
                content = read_docx(file_path)
            else:
                content = read_txt(file_path)
        except Exception as exc:
            interview_skipped.append(f"{file_path.name}（读取失败：{exc}）")
            continue
        
        if not content:
            interview_skipped.append(f"{file_path.name}（内容为空）")
            continue
        
        header = f"--- {file_path.name} ---"
        interview_sections.append(f"{header}\n{content.strip()}")
    
    print(f"✓ 读取访谈文件: {len(interview_sections)} 个")
    if interview_skipped:
        print(f"⚠️  跳过 {len(interview_skipped)} 个文件")
    
    # 3. 读取案例文件
    print("\n" + "="*60)
    print("步骤3: 读取案例文件")
    print("="*60)
    case_files = collect_case_files(county_dir)
    if not case_files:
        print("⚠️  未找到案例文件")
    
    case_sections: List[str] = []
    case_skipped: List[str] = []
    
    for file_path in case_files:
        try:
            content = read_docx(file_path)
        except Exception as exc:
            case_skipped.append(f"{file_path.name}（读取失败：{exc}）")
            continue
        
        if not content:
            case_skipped.append(f"{file_path.name}（内容为空）")
            continue
        
        header = f"--- {file_path.name} ---"
        case_sections.append(f"{header}\n{content.strip()}")
    
    print(f"✓ 读取案例文件: {len(case_sections)} 个")
    if case_skipped:
        print(f"⚠️  跳过 {len(case_skipped)} 个文件")
    
    # 4. 组合所有内容
    print("\n" + "="*60)
    print("步骤4: 合并所有内容")
    print("="*60)
    
    final_sections = []
    
    # 添加基础信息
    if basic_info:
        final_sections.append(f"【县域基础信息】\n{basic_info}")
    
    # 添加访谈记录
    if interview_sections:
        interview_content = "\n\n".join(interview_sections)
        final_sections.append(f"【访谈记录】\n{interview_content}")
    
    # 添加案例补充
    if case_sections:
        case_content = "\n\n".join(case_sections)
        final_sections.append(f"【案例补充】\n{case_content}")
    
    if not final_sections:
        raise FileNotFoundError(f"未找到任何有效内容: {county_dir}")
    
    # 保存
    output_file.parent.mkdir(parents=True, exist_ok=True)
    merged_content = "\n\n".join(final_sections)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(merged_content)
    
    print(f"\n✅ 合并完成 → {output_file}")
    print(f"   - 基础信息: {'✓' if basic_info else '✗'}")
    print(f"   - 访谈文件: {len(interview_sections)} 个")
    print(f"   - 案例文件: {len(case_sections)} 个")
    print(f"   - 总字符数: {len(merged_content)}")
    print("="*60)


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



