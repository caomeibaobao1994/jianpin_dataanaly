#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动发现并批量处理所有县的标签生成脚本

功能：
- 自动扫描 input_text 目录下的所有县目录
- 检查是否有基础信息.txt 和访谈文本
- 批量处理所有符合条件的县
- 支持跳过已处理、错误重试、进度记录等功能

用法：
    # 处理所有县
    python process_all_counties.py

    # 只处理前10个县（测试用）
    python process_all_counties.py --limit 10

    # 跳过已处理的县
    python process_all_counties.py --skip-existing

    # 强制重新处理所有县
    python process_all_counties.py --force

    # 只检查，不实际处理
    python process_all_counties.py --dry-run
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

INPUT_BASE = Path(__file__).parent / "input_text"
SCRIPT_PATH = Path(__file__).parent / "county_labeler.py"
OUTPUT_DIR = Path(__file__).parent / "output" / "4_poverty_reduction_summary"
LOG_FILE = Path(__file__).parent / "output" / "batch_processing_log.txt"


def find_text_dir(county_dir: Path) -> Optional[Path]:
    """查找县的文本目录"""
    # 常见的文本目录名称模式（按优先级）
    patterns = [
        f"{county_dir.name}-文本",  # 习水县模式
        f"{county_dir.name}文本",   # 张北县、天柱县模式
        f"{county_dir.name} 文本",  # 惠水县模式（有空格）
        "*文本*",                   # 通用模式
        "*文本",                    # 通用模式
    ]
    
    for pattern in patterns:
        matches = list(county_dir.glob(pattern))
        for match in matches:
            if match.is_dir():
                # 检查目录中是否有docx或txt文件
                if any(match.rglob("*.docx")) or any(match.rglob("*.txt")):
                    return match
    
    # 如果没找到特定文本目录，检查县目录本身是否包含docx文件
    if any(county_dir.rglob("*.docx")):
        return county_dir
    
    return None


def check_county(county_dir: Path) -> Tuple[bool, str, Optional[Path]]:
    """检查县目录是否存在且有效"""
    if not county_dir.exists():
        return False, f"目录不存在", None
    
    if not county_dir.is_dir():
        return False, f"不是目录", None
    
    base_info = county_dir / "基础信息.txt"
    if not base_info.exists():
        return False, f"缺少基础信息.txt", None
    
    text_dir = find_text_dir(county_dir)
    if text_dir is None:
        return False, f"未找到文本目录或docx文件", None
    
    return True, "OK", text_dir


def is_already_processed(county_name: str) -> bool:
    """检查县是否已经处理过"""
    output_file = OUTPUT_DIR / f"{county_name}_labels.json"
    return output_file.exists()


def process_county(
    county_dir: Path,
    char_limit: int = 50000,
    force: bool = False,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """处理单个县"""
    county_name = county_dir.name
    
    # 检查是否已处理
    if not force and is_already_processed(county_name):
        return False, "已处理（跳过）"
    
    # 验证县目录
    is_valid, msg, text_dir = check_county(county_dir)
    if not is_valid:
        return False, msg
    
    if dry_run:
        return True, f"待处理（文本目录: {text_dir.name}）"
    
    # 构建命令
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--county-dir", str(county_dir),
        "--text-dir", str(text_dir),
        "--char-limit", str(char_limit)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300  # 5分钟超时
        )
        return True, "成功"
    except subprocess.TimeoutExpired:
        return False, "超时（>5分钟）"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else "未知错误"
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        return False, f"失败: {error_msg}"
    except Exception as e:
        return False, f"异常: {str(e)[:200]}"


def scan_all_counties() -> list[Path]:
    """扫描所有县目录"""
    if not INPUT_BASE.exists():
        raise FileNotFoundError(f"输入目录不存在: {INPUT_BASE}")
    
    counties = []
    for item in INPUT_BASE.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            counties.append(item)
    
    return sorted(counties)


def log_result(county_name: str, status: str, message: str, log_file: Path):
    """记录处理结果到日志文件"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {status:6s} | {county_name:50s} | {message}\n")


def main():
    parser = argparse.ArgumentParser(
        description="自动发现并批量处理所有县的标签生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 处理所有县
  python process_all_counties.py

  # 只处理前10个县（测试）
  python process_all_counties.py --limit 10

  # 跳过已处理的县
  python process_all_counties.py --skip-existing

  # 强制重新处理所有县
  python process_all_counties.py --force

  # 只检查，不实际处理
  python process_all_counties.py --dry-run
        """
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="限制处理的县数量（用于测试）"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="跳过已处理的县（默认行为）"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新处理所有县（即使已处理过）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只检查，不实际处理"
    )
    parser.add_argument(
        "--char-limit",
        type=int,
        default=50000,
        help="访谈文本字符数限制（默认50000）"
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=LOG_FILE,
        help=f"日志文件路径（默认: {LOG_FILE}）"
    )
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    
    # 初始化日志文件
    if args.log.exists():
        args.log.unlink()  # 删除旧日志
    log_result("COUNTY", "STATUS", "MESSAGE", args.log)
    
    # 扫描所有县
    print("🔍 正在扫描县目录...")
    all_counties = scan_all_counties()
    
    if args.limit:
        all_counties = all_counties[:args.limit]
        print(f"📌 限制处理数量: {args.limit}")
    
    total = len(all_counties)
    print(f"✅ 发现 {total} 个县目录\n")
    
    # 统计信息
    stats = {
        "total": total,
        "valid": 0,
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "dry_run": 0
    }
    
    # 处理每个县
    for i, county_dir in enumerate(all_counties, 1):
        county_name = county_dir.name
        prefix = f"[{i}/{total}]"
        
        print(f"{prefix} 处理: {county_name}")
        
        # 检查有效性
        is_valid, msg, _ = check_county(county_dir)
        if not is_valid:
            print(f"     ❌ 无效: {msg}")
            log_result(county_name, "INVALID", msg, args.log)
            continue
        
        stats["valid"] += 1
        
        # 检查是否已处理
        if not args.force and is_already_processed(county_name):
            print(f"     ⏭️  跳过: 已处理")
            log_result(county_name, "SKIPPED", "已处理", args.log)
            stats["skipped"] += 1
            continue
        
        # 处理县
        success, message = process_county(
            county_dir,
            char_limit=args.char_limit,
            force=args.force,
            dry_run=args.dry_run
        )
        
        if args.dry_run:
            print(f"     ✓ 待处理: {message}")
            log_result(county_name, "DRY_RUN", message, args.log)
            stats["dry_run"] += 1
        elif success:
            print(f"     ✅ 成功")
            log_result(county_name, "SUCCESS", message, args.log)
            stats["processed"] += 1
        else:
            print(f"     ❌ {message}")
            log_result(county_name, "FAILED", message, args.log)
            stats["failed"] += 1
        
        # 添加小延迟，避免API调用过快
        if not args.dry_run and i < total:
            time.sleep(1)
    
    # 打印统计信息
    print(f"\n{'='*80}")
    print("📊 处理统计")
    print(f"{'='*80}")
    print(f"总目录数:    {stats['total']}")
    print(f"有效县数:    {stats['valid']}")
    if args.dry_run:
        print(f"待处理数:    {stats['dry_run']}")
    else:
        print(f"成功处理:    {stats['processed']}")
        print(f"已跳过:      {stats['skipped']}")
        print(f"失败数量:    {stats['failed']}")
    print(f"\n📝 详细日志已保存到: {args.log}")
    print(f"{'='*80}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 运行失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

