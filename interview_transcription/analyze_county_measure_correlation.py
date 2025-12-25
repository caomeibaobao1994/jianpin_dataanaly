#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析县域标签与措施标签的关联关系
用于识别不同类型县在减贫措施上的差异
"""

import json
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set
import math

OUTPUT_DIR = Path(__file__).parent / "output" / "4_poverty_reduction_summary"

# 重点县域标签（按频率排序）
KEY_COUNTY_TAGS = [
    "特色产业县", "山区县", "民族聚居县", "定点帮扶县", 
    "旅游县", "东西部协作重点县", "易地搬迁重点县", "农业大县"
]

# 标准措施标签类别
MEASURE_CATEGORIES = {
    "产业扶贫": ["产业扶贫", "特色产业", "合作社", "龙头企业带动", "土地流转", "职业经理人模式"],
    "基础设施": ["基础设施建设", "道路建设", "饮水安全", "电网改造", "网络覆盖", "危房改造"],
    "教育扶贫": ["教育扶贫", "教育支持", "雨露计划", "助学补贴", "职业教育", "控辍保学"],
    "医疗扶贫": ["医疗保障", "医疗救助", "健康帮扶", "家庭医生", "医保报销"],
    "就业扶贫": ["就业帮扶", "技能培训", "劳务输出", "家门口就业", "稳岗补贴"],
    "易地搬迁": ["易地搬迁", "集中安置", "搬迁后续扶持"],
    "社会保障": ["社会保障", "低保兜底", "特困救助", "养老保险", "临时救助"],
    "金融支持": ["金融支持", "小额信贷", "贴息贷款", "金融保险"],
    "组织保障": ["驻村帮扶", "第一书记", "帮扶干部", "基层党建", "党组织作用"],
    "机制创新": ["精准识别", "动态监测", "督导机制", "问责监督", "干群关系"],
    "协作帮扶": ["东西部协作", "定点帮扶", "对口支援", "社会帮扶"],
    "其他": ["思想扶贫", "内生动力", "移风易俗", "政策感恩"]
}

# 措施标签到类别的映射
MEASURE_TAG_TO_CATEGORY = {}
for category, tags in MEASURE_CATEGORIES.items():
    for tag in tags:
        MEASURE_TAG_TO_CATEGORY[tag] = category


def load_all_labels() -> List[Dict]:
    """加载所有县的标签文件"""
    labels_files = list(OUTPUT_DIR.glob("*_labels.json"))
    results = []
    
    for file_path in labels_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_file'] = file_path.name
                results.append(data)
        except Exception as e:
            print(f"⚠️  读取失败: {file_path.name} - {e}")
    
    return results


def analyze_correlation(all_data: List[Dict]) -> Dict:
    """分析县域标签与措施标签的关联关系"""
    
    # 统计每个县域标签对应的措施标签分布（按县计数，不是按措施计数）
    county_tag_to_measures = defaultdict(lambda: defaultdict(set))  # 使用set避免重复计数
    county_tag_to_categories = defaultdict(lambda: defaultdict(set))
    
    # 统计每个县域标签的县数量
    county_tag_counts = Counter()
    
    # 统计总体措施标签分布（按县计数）
    overall_measures = defaultdict(set)
    overall_categories = defaultdict(set)
    
    for data in all_data:
        county_name = data.get('county_name', '')
        county_tags = data.get('county_tags', [])
        effective_measures = data.get('effective_measures', [])
        
        # 收集该县的所有措施类别
        county_categories = set()
        for measure in effective_measures:
            if isinstance(measure, dict):
                tag = measure.get('tag', '')
                if tag:
                    category = MEASURE_TAG_TO_CATEGORY.get(tag, '其他')
                    county_categories.add(category)
                    overall_measures[tag].add(county_name)
                    overall_categories[category].add(county_name)
        
        # 统计每个县域标签对应的措施分布
        for county_tag in county_tags:
            county_tag_counts[county_tag] += 1
            
            for measure in effective_measures:
                if isinstance(measure, dict):
                    tag = measure.get('tag', '')
                    if tag:
                        category = MEASURE_TAG_TO_CATEGORY.get(tag, '其他')
                        county_tag_to_measures[county_tag][tag].add(county_name)
                        county_tag_to_categories[county_tag][category].add(county_name)
    
    # 转换为计数
    county_tag_to_measures_count = {}
    for county_tag, measures in county_tag_to_measures.items():
        county_tag_to_measures_count[county_tag] = {tag: len(counties) for tag, counties in measures.items()}
    
    county_tag_to_categories_count = {}
    for county_tag, categories in county_tag_to_categories.items():
        county_tag_to_categories_count[county_tag] = {cat: len(counties) for cat, counties in categories.items()}
    
    overall_measures_count = {tag: len(counties) for tag, counties in overall_measures.items()}
    overall_categories_count = {cat: len(counties) for cat, counties in overall_categories.items()}
    
    total_counties = len(all_data)
    
    return {
        'county_tag_counts': county_tag_counts,
        'county_tag_to_measures': county_tag_to_measures_count,
        'county_tag_to_categories': county_tag_to_categories_count,
        'overall_measures': overall_measures_count,
        'overall_categories': overall_categories_count,
        'total_counties': total_counties
    }


def calculate_significance(county_tag: str, measure_category: str, stats: Dict) -> Dict:
    """计算显著性差异（使用卡方检验的简化版本）"""
    
    county_count = stats['county_tag_counts'].get(county_tag, 0)
    if county_count == 0:
        return {'significant': False, 'ratio': 0, 'overall_ratio': 0}
    
    total_counties = stats['total_counties']
    
    # 该县域标签中该措施类别的出现次数
    county_with_measure = stats['county_tag_to_categories'][county_tag].get(measure_category, 0)
    county_ratio = county_with_measure / county_count if county_count > 0 else 0
    
    # 总体中该措施类别的出现次数
    overall_with_measure = stats['overall_categories'].get(measure_category, 0)
    overall_ratio = overall_with_measure / total_counties if total_counties > 0 else 0
    
    # 计算差异（简化版，实际应该用卡方检验）
    diff = county_ratio - overall_ratio
    diff_percent = diff * 100
    
    # 简单的显著性判断：差异超过10个百分点认为显著
    significant = abs(diff_percent) > 10
    
    return {
        'significant': significant,
        'county_ratio': county_ratio,
        'overall_ratio': overall_ratio,
        'diff_percent': diff_percent,
        'county_count': county_count,
        'county_with_measure': county_with_measure
    }


def generate_correlation_report(stats: Dict) -> str:
    """生成关联分析报告"""
    lines = []
    lines.append("=" * 80)
    lines.append("县域标签与减贫措施关联分析报告")
    lines.append("=" * 80)
    lines.append(f"\n总县数: {stats['total_counties']}")
    
    # 总体措施类别分布
    lines.append("\n" + "=" * 80)
    lines.append("一、总体措施类别分布（基准）")
    lines.append("=" * 80)
    total = stats['total_counties']
    for category, count in sorted(stats['overall_categories'].items(), key=lambda x: x[1], reverse=True):
        ratio = count / total * 100
        lines.append(f"  {category:20s} : {count:3d} 个县 ({ratio:5.1f}%)")
    
    # 重点县域标签的分析
    lines.append("\n" + "=" * 80)
    lines.append("二、重点县域标签对应的措施类别分布")
    lines.append("=" * 80)
    
    for county_tag in KEY_COUNTY_TAGS:
        county_count = stats['county_tag_counts'].get(county_tag, 0)
        if county_count == 0:
            continue
        
        lines.append(f"\n【{county_tag}】（{county_count}个县）")
        lines.append("-" * 80)
        
        # 该县域标签的措施类别分布
        category_stats = stats['county_tag_to_categories'][county_tag]
        
        # 按出现频率排序
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
        
        lines.append(f"{'措施类别':<20s} {'出现次数':<10s} {'占比':<10s} {'总体占比':<10s} {'差异':<10s} {'显著性'}")
        lines.append("-" * 80)
        
        for category, count in sorted_categories:
            ratio = count / county_count * 100
            overall_count = stats['overall_categories'].get(category, 0)
            overall_ratio = overall_count / stats['total_counties'] * 100
            diff = ratio - overall_ratio
            
            sig_info = calculate_significance(county_tag, category, stats)
            sig_mark = "★" if sig_info['significant'] else ""
            
            lines.append(f"{category:<20s} {count:<10d} {ratio:>6.1f}%    {overall_ratio:>6.1f}%    {diff:>+6.1f}%    {sig_mark}")
    
    # 显著性差异总结
    lines.append("\n" + "=" * 80)
    lines.append("三、显著性差异总结（差异>10个百分点）")
    lines.append("=" * 80)
    
    significant_findings = []
    for county_tag in KEY_COUNTY_TAGS:
        county_count = stats['county_tag_counts'].get(county_tag, 0)
        if county_count == 0:
            continue
        
        for category in MEASURE_CATEGORIES.keys():
            sig_info = calculate_significance(county_tag, category, stats)
            if sig_info['significant']:
                significant_findings.append({
                    'county_tag': county_tag,
                    'category': category,
                    'county_ratio': sig_info['county_ratio'] * 100,
                    'overall_ratio': sig_info['overall_ratio'] * 100,
                    'diff': sig_info['diff_percent']
                })
    
    if significant_findings:
        # 按差异绝对值排序
        significant_findings.sort(key=lambda x: abs(x['diff']), reverse=True)
        
        lines.append(f"\n共发现 {len(significant_findings)} 个显著性差异：\n")
        lines.append(f"{'县域标签':<20s} {'措施类别':<20s} {'该类型占比':<12s} {'总体占比':<12s} {'差异':<10s}")
        lines.append("-" * 80)
        
        for finding in significant_findings:
            lines.append(
                f"{finding['county_tag']:<20s} "
                f"{finding['category']:<20s} "
                f"{finding['county_ratio']:>6.1f}%      "
                f"{finding['overall_ratio']:>6.1f}%      "
                f"{finding['diff']:>+6.1f}%"
            )
    else:
        lines.append("\n未发现显著性差异（差异>10个百分点）")
    
    # 关键发现
    lines.append("\n" + "=" * 80)
    lines.append("四、关键发现与政策启示")
    lines.append("=" * 80)
    
    # 分析每个重点县域标签的特点
    for county_tag in KEY_COUNTY_TAGS:
        county_count = stats['county_tag_counts'].get(county_tag, 0)
        if county_count == 0:
            continue
        
        category_stats = stats['county_tag_to_categories'][county_tag]
        
        lines.append(f"\n【{county_tag}】（{county_count}个县）")
        lines.append(f"  特点：")
        
        # 找出显著高于或低于总体的措施类别
        significant_categories = []
        for category, count in category_stats.items():
            ratio = count / county_count * 100
            overall_count = stats['overall_categories'].get(category, 0)
            overall_ratio = overall_count / stats['total_counties'] * 100
            diff = ratio - overall_ratio
            
            if abs(diff) > 5:  # 差异超过5个百分点
                significant_categories.append((category, ratio, overall_ratio, diff))
        
        # 按差异绝对值排序
        significant_categories.sort(key=lambda x: abs(x[3]), reverse=True)
        
        if significant_categories:
            for category, ratio, overall_ratio, diff in significant_categories[:5]:  # 只显示前5个
                lines.append(f"    - {category}: {ratio:.1f}%（总体{overall_ratio:.1f}%，{'显著高于' if diff > 0 else '显著低于'}总体{abs(diff):.1f}个百分点）")
        else:
            lines.append(f"    - 措施分布与总体基本一致，无明显差异")
    
    return "\n".join(lines)


def main():
    print("🔍 正在加载所有县的标签数据...")
    all_data = load_all_labels()
    print(f"✅ 成功加载 {len(all_data)} 个县的数据")
    
    print("\n📊 正在分析县域标签与措施标签的关联关系...")
    stats = analyze_correlation(all_data)
    
    print("\n📝 正在生成关联分析报告...")
    report = generate_correlation_report(stats)
    
    # 保存报告
    report_file = Path(__file__).parent / "output" / "county_measure_correlation_report.txt"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 关联分析报告已保存: {report_file}")
    
    # 打印报告摘要
    print("\n" + "=" * 80)
    print("报告摘要")
    print("=" * 80)
    print(report[:3000])  # 打印前3000字符
    print("\n... (完整报告请查看文件)")


if __name__ == "__main__":
    main()

