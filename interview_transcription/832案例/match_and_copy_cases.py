#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
832案例匹配与复制工具

功能：
1. 扫描input_text目录中的所有县文件夹
2. 从案例补充文件夹中查找匹配的案例文档
3. 将匹配的案例复制到对应县的文件夹中

用法：
    python match_and_copy_cases.py
    python match_and_copy_cases.py --dry-run  # 预览模式
"""

import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


class CountyCaseMatcher:
    """县案例匹配器"""
    
    def __init__(self, input_text_dir: Path, case_dir: Path):
        self.input_text_dir = input_text_dir
        self.case_dir = case_dir
        
    def extract_county_from_dirname(self, dirname: str) -> Optional[str]:
        """
        从input_text的文件夹名中提取县名
        
        支持的格式：
        - 0518工布江达县
        - 0714-0715河北省平乡县
        - 云南省文山州丘北县（20250108-0109）
        - 贵州省铜仁市沿河土家族自治县（20240805-20240811）
        - 20240723-240724贵州-遵义市-正安县
        - 0809六枝特区（贵州省六盘水市）
        """
        # 移除日期部分（各种格式）
        # 格式1: 开头的日期 MMDD 或 MMDD-DDDD
        text = re.sub(r'^\d{4}(-\d{4})?', '', dirname)
        # 格式2: 开头的 YYYYMMDD-YYYYMMDD
        text = re.sub(r'^\d{8}-\d{8}', '', text)
        # 格式3: 开头的 YYYYMMDD-MMDD
        text = re.sub(r'^\d{8}-\d{4}', '', text)
        # 格式4: 括号内的所有内容（包括日期和地名）
        text = re.sub(r'[（(][^）)]+[）)]', '', text)
        # 格式5: 开头的纯数字
        text = re.sub(r'^\d+', '', text)
        
        # 移除其他干扰字符
        text = text.strip('- ')
        
        # 提取县名的多种模式（优先级从高到低）
        patterns = [
            # 省+州+县（如：云南省文山州丘北县）
            r'([\u4e00-\u9fa5]+省)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]+州)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]+(县|自治县|市|区|旗|自治旗|特区))',
            # 省+市+县（完整）
            r'([\u4e00-\u9fa5]+省)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]+市)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]+(县|自治县|市|区|旗|自治旗|特区))',
            # 州+县（如：文山州丘北县）
            r'([\u4e00-\u9fa5]+州)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]+(县|自治县|市|区|旗|自治旗|特区))',
            # 省+县
            r'([\u4e00-\u9fa5]+省)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]+(县|自治县|市|区|旗|自治旗|特区))',
            # 市+县
            r'([\u4e00-\u9fa5]+市)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]+(县|自治县|市|区|旗|自治旗|特区))',
            # 只有县名
            r'([\u4e00-\u9fa5]{2,}(县|自治县|区|旗|自治旗|特区|市))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                # 返回最后一个分组（县名），并确保去掉州前缀
                county = groups[-2] if len(groups) > 1 else groups[0]
                # 如果县名中还包含"州"，移除它
                county = re.sub(r'^[\u4e00-\u9fa5]+州', '', county)
                return county
        
        return None
    
    def normalize_county_name(self, county_name: str) -> str:
        """
        标准化县名，用于匹配
        
        规则：
        - 移除省市州前缀
        - 统一后缀（县/市/区/旗等）
        """
        name = county_name
        
        # 移除省市州前缀（带或不带"省"/"市"/"州"字）
        # 先移除完整的"XX省XX市"格式
        name = re.sub(r'^[\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+市', '', name)
        # 再移除单独的"XX省"或"XX市"或"XX州"
        name = re.sub(r'^[\u4e00-\u9fa5]+(省|市|州)', '', name)
        # 移除不带后缀的省名（如"河北"、"广西"等）
        name = re.sub(r'^(河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|海南|四川|贵州|云南|陕西|甘肃|青海|台湾|广西|西藏|宁夏|新疆|内蒙古)', '', name)
        
        return name.strip()
    
    def extract_county_core(self, county_name: str) -> Optional[str]:
        """
        提取县名核心部分（用于处理如"退耕还林政策下水城区"这类情况）
        
        返回: 县名核心（如"水城"），如果无法提取则返回None
        """
        # 查找县名后缀
        suffixes = ['自治县', '自治旗', '特区', '县', '市', '区', '旗']
        for suffix in suffixes:
            if county_name.endswith(suffix) or county_name.endswith(suffix + '_1') or county_name.endswith(suffix + '_2'):
                # 移除后缀和序号
                core = re.sub(r'(' + re.escape(suffix) + r')(?:_\d+)?$', '', county_name)
                # 如果核心部分太长（>8个字），可能包含描述性文字，取最后2-4个字
                if len(core) > 8:
                    core = core[-4:] if len(core[-4:]) > 2 else core[-2:]
                return core
        return None
    
    def find_matching_case(self, county_name: str) -> List[Path]:
        """
        在案例补充文件夹中查找匹配的案例
        
        返回: 匹配的案例文件路径列表
        """
        if not self.case_dir.exists():
            return []
        
        # 标准化县名用于匹配
        normalized_county = self.normalize_county_name(county_name)
        
        # 提取县名核心部分（去掉后缀）
        county_core = re.sub(r'(县|自治县|市|区|旗|自治旗|特区)$', '', normalized_county)
        
        matching_files = []
        
        # 遍历案例补充文件夹中的所有文件
        for case_file in self.case_dir.glob("*.docx"):
            case_filename = case_file.stem  # 不含扩展名的文件名
            
            # 标准化案例文件名
            normalized_case = self.normalize_county_name(case_filename)
            
            # 提取案例文件名核心部分
            case_core = re.sub(r'(县|自治县|市|区|旗|自治旗|特区)$', '', normalized_case)
            
            # 跳过明显不匹配的（名字太短或差异太大）
            if len(case_core) < 2 or len(county_core) < 2:
                continue
            
            # 匹配策略1: 完全匹配（最精确）
            if normalized_county == normalized_case:
                matching_files.append(case_file)
                continue
            
            # 匹配策略2: 核心名称完全匹配（处理"县"vs"市"等情况）
            if county_core == case_core and len(county_core) >= 2:
                matching_files.append(case_file)
                continue
            
            # 匹配策略3: 完整县名包含匹配（处理"退耕还林政策下水城区"这类情况）
            # 检查案例文件名是否包含查找的县名
            if len(normalized_county) >= 3 and normalized_county in normalized_case:
                matching_files.append(case_file)
                continue
            
            # 匹配策略4: 县名核心在案例中
            # 2个字的县名也很常见（如务川、灵璧等），但要避免单字匹配
            if len(county_core) >= 2 and county_core in case_core:
                # 如果县名只有2个字，确保是完整匹配或案例以此开头
                if len(county_core) == 2:
                    if case_core == county_core or case_core.startswith(county_core):
                        matching_files.append(case_file)
                        continue
                else:
                    matching_files.append(case_file)
                    continue
            
            # 匹配策略5: 案例核心在县名中
            # 允许2个字的案例名，但需要完整匹配或县名以此开头
            if len(case_core) >= 2 and case_core in county_core:
                if len(case_core) == 2:
                    if county_core == case_core or county_core.startswith(case_core):
                        matching_files.append(case_file)
                        continue
                else:
                    matching_files.append(case_file)
                    continue
        
        return matching_files
    
    def copy_case_to_county(
        self, 
        case_file: Path, 
        county_dir: Path,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        复制案例文件到县文件夹
        
        返回: (成功标志, 消息)
        """
        target_file = county_dir / case_file.name
        
        # 检查目标文件是否已存在
        if target_file.exists():
            return False, "文件已存在"
        
        if dry_run:
            return True, f"[预览] 将复制到: {target_file.name}"
        
        try:
            shutil.copy2(case_file, target_file)
            return True, f"✅ 已复制: {case_file.name}"
        except Exception as e:
            return False, f"❌ 复制失败: {e}"
    
    def process_all_counties(self, dry_run: bool = False) -> Dict:
        """
        处理所有县文件夹
        
        返回: 处理结果字典
        """
        results = {
            "total_counties": 0,
            "matched_counties": 0,
            "unmatched_counties": 0,
            "total_cases_copied": 0,
            "details": []
        }
        
        # 获取所有县文件夹
        county_dirs = sorted([d for d in self.input_text_dir.iterdir() if d.is_dir()])
        results["total_counties"] = len(county_dirs)
        
        print(f"\n{'='*80}")
        print(f"开始匹配处理...")
        print(f"{'='*80}")
        print(f"📂 Input目录: {self.input_text_dir}")
        print(f"📁 案例目录: {self.case_dir}")
        print(f"📊 县文件夹数量: {len(county_dirs)}")
        print(f"🔍 模式: {'预览模式（不复制文件）' if dry_run else '正式模式（将复制文件）'}")
        print()
        
        for county_dir in county_dirs:
            dirname = county_dir.name
            
            # 提取县名
            county_name = self.extract_county_from_dirname(dirname)
            
            if not county_name:
                print(f"\n⚠️  无法提取县名: {dirname}")
                results["unmatched_counties"] += 1
                results["details"].append({
                    "文件夹": dirname,
                    "提取县名": None,
                    "匹配案例": 0,
                    "状态": "未提取县名"
                })
                continue
            
            # 查找匹配的案例
            matching_cases = self.find_matching_case(county_name)
            
            if not matching_cases:
                print(f"\n❌ 未找到匹配: {dirname}")
                print(f"   提取县名: {county_name}")
                results["unmatched_counties"] += 1
                results["details"].append({
                    "文件夹": dirname,
                    "提取县名": county_name,
                    "匹配案例": 0,
                    "状态": "未找到匹配"
                })
                continue
            
            # 找到匹配
            print(f"\n✅ 找到匹配: {dirname}")
            print(f"   提取县名: {county_name}")
            print(f"   匹配案例数: {len(matching_cases)}")
            
            results["matched_counties"] += 1
            copied_count = 0
            
            for case_file in matching_cases:
                success, msg = self.copy_case_to_county(case_file, county_dir, dry_run)
                print(f"   {msg}")
                if success:
                    copied_count += 1
            
            results["total_cases_copied"] += copied_count
            results["details"].append({
                "文件夹": dirname,
                "提取县名": county_name,
                "匹配案例": len(matching_cases),
                "复制成功": copied_count,
                "案例文件": [f.name for f in matching_cases],
                "状态": "成功"
            })
        
        return results


def generate_report(results: Dict, output_path: Path):
    """生成处理报告"""
    report_lines = [
        "=" * 80,
        "832案例匹配与复制报告",
        "=" * 80,
        "",
        "📊 统计摘要",
        "-" * 80,
        f"总县数: {results['total_counties']}",
        f"匹配成功: {results['matched_counties']}",
        f"未匹配: {results['unmatched_counties']}",
        f"复制案例数: {results['total_cases_copied']}",
        f"匹配率: {results['matched_counties']/results['total_counties']*100:.1f}%" if results['total_counties'] > 0 else "匹配率: 0%",
        "",
        "📋 详细列表",
        "-" * 80,
    ]
    
    # 按状态分组
    matched = [d for d in results['details'] if d['状态'] == '成功']
    unmatched = [d for d in results['details'] if d['状态'] == '未找到匹配']
    no_extract = [d for d in results['details'] if d['状态'] == '未提取县名']
    
    # 匹配成功的
    if matched:
        report_lines.append("\n【匹配成功的县】")
        for detail in matched:
            report_lines.append(f"\n✅ {detail['文件夹']}")
            report_lines.append(f"   县名: {detail['提取县名']}")
            report_lines.append(f"   匹配案例: {detail['匹配案例']}个")
            report_lines.append(f"   复制成功: {detail['复制成功']}个")
            for case_file in detail['案例文件']:
                report_lines.append(f"   - {case_file}")
    
    # 未找到匹配的
    if unmatched:
        report_lines.append("\n【未找到匹配的县】")
        for detail in unmatched:
            report_lines.append(f"\n❌ {detail['文件夹']}")
            report_lines.append(f"   县名: {detail['提取县名']}")
    
    # 未提取县名的
    if no_extract:
        report_lines.append("\n【未能提取县名的文件夹】")
        for detail in no_extract:
            report_lines.append(f"\n⚠️  {detail['文件夹']}")
    
    report_text = "\n".join(report_lines)
    
    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    # 同时保存JSON格式
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 报告已保存:")
    print(f"  - 文本格式: {output_path}")
    print(f"  - JSON格式: {json_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="832案例匹配与复制工具")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际复制文件")
    parser.add_argument(
        "--input-dir", 
        type=str, 
        default="../input_text",
        help="input_text目录路径（默认: ../input_text）"
    )
    parser.add_argument(
        "--case-dir", 
        type=str, 
        default="./案例补充",
        help="案例补充目录路径（默认: ./案例补充）"
    )
    args = parser.parse_args()
    
    # 设置路径
    script_dir = Path(__file__).parent
    input_text_dir = (script_dir / args.input_dir).resolve()
    case_dir = (script_dir / args.case_dir).resolve()
    
    # 检查目录是否存在
    if not input_text_dir.exists():
        print(f"❌ input_text目录不存在: {input_text_dir}")
        return
    
    if not case_dir.exists():
        print(f"❌ 案例补充目录不存在: {case_dir}")
        print(f"💡 提示: 请先运行 extract_and_rename_cases.py 生成案例补充文件夹")
        return
    
    print("=" * 80)
    print("🚀 832案例匹配与复制工具")
    print("=" * 80)
    print(f"📂 Input目录: {input_text_dir}")
    print(f"📁 案例目录: {case_dir}")
    print(f"🔍 模式: {'预览模式（不复制文件）' if args.dry_run else '正式模式（将复制文件）'}")
    print()
    
    # 创建匹配器并处理
    matcher = CountyCaseMatcher(input_text_dir, case_dir)
    results = matcher.process_all_counties(dry_run=args.dry_run)
    
    # 生成报告
    print(f"\n{'='*80}")
    print("📊 处理完成")
    print(f"{'='*80}")
    print(f"总县数: {results['total_counties']}")
    print(f"匹配成功: {results['matched_counties']}")
    print(f"未匹配: {results['unmatched_counties']}")
    print(f"复制案例数: {results['total_cases_copied']}")
    print(f"匹配率: {results['matched_counties']/results['total_counties']*100:.1f}%" if results['total_counties'] > 0 else "匹配率: 0%")
    
    if not args.dry_run:
        report_path = script_dir / "匹配报告.txt"
        generate_report(results, report_path)
    else:
        print("\n💡 提示: 使用 --dry-run 选项预览结果，去掉该选项后将实际复制文件")


if __name__ == "__main__":
    main()

