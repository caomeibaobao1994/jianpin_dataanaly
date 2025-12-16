#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析所有县的标签，汇总并评估合理性，提出标准化建议
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set

OUTPUT_DIR = Path(__file__).parent / "output" / "4_poverty_reduction_summary"


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


def extract_all_tags(all_data: List[Dict]) -> Dict[str, Dict]:
    """提取所有标签并统计"""
    county_tags_counter = Counter()
    measure_tags_counter = Counter()
    tag_to_counties = defaultdict(set)  # 每个tag出现在哪些县
    measure_tag_to_counties = defaultdict(set)
    
    for data in all_data:
        county_name = data.get('county_name', '未知')
        
        # 统计县域标签
        county_tags = data.get('county_tags', [])
        for tag in county_tags:
            county_tags_counter[tag] += 1
            tag_to_counties[tag].add(county_name)
        
        # 统计措施标签
        effective_measures = data.get('effective_measures', [])
        for measure in effective_measures:
            if isinstance(measure, dict):
                tag = measure.get('tag', '')
                if tag:
                    measure_tags_counter[tag] += 1
                    measure_tag_to_counties[tag].add(county_name)
    
    return {
        'county_tags': {
            'counter': county_tags_counter,
            'to_counties': tag_to_counties
        },
        'measure_tags': {
            'counter': measure_tags_counter,
            'to_counties': measure_tag_to_counties
        }
    }


def analyze_tag_patterns(tags: Counter) -> Dict:
    """分析标签模式"""
    patterns = {
        '地形类': [],
        '区位类': [],
        '产业类': [],
        '政策类': [],
        '其他': []
    }
    
    # 地形关键词
    terrain_keywords = ['山', '高原', '平原', '丘陵', '盆地', '河谷', '边境', '沿海']
    # 区位关键词
    location_keywords = ['革命老区', '民族', '边境', '易地搬迁', '生态脆弱']
    # 产业关键词
    industry_keywords = ['产业', '农业', '工业', '旅游', '电商', '光伏', '养殖', '种植']
    # 政策关键词
    policy_keywords = ['扶贫', '协作', '帮扶', '定点', '示范']
    
    for tag, count in tags.items():
        categorized = False
        
        # 地形类
        if any(kw in tag for kw in terrain_keywords):
            patterns['地形类'].append((tag, count))
            categorized = True
        
        # 区位类
        if not categorized and any(kw in tag for kw in location_keywords):
            patterns['区位类'].append((tag, count))
            categorized = True
        
        # 产业类
        if not categorized and any(kw in tag for kw in industry_keywords):
            patterns['产业类'].append((tag, count))
            categorized = True
        
        # 政策类
        if not categorized and any(kw in tag for kw in policy_keywords):
            patterns['政策类'].append((tag, count))
            categorized = True
        
        # 其他
        if not categorized:
            patterns['其他'].append((tag, count))
    
    return patterns


def suggest_standardized_tags(county_tags: Counter, measure_tags: Counter) -> Dict:
    """建议标准化的标签体系"""
    
    # 县域标签标准化建议
    county_tag_categories = {
        '地形特征': [
            '山区县', '高原县', '平原县', '丘陵县', '盆地县', '河谷县'
        ],
        '区位特征': [
            '革命老区县', '民族聚居县', '边境县', '易地搬迁重点县', 
            '生态脆弱区', '资源型县', '农业大县'
        ],
        '产业特征': [
            '农业县', '工业县', '旅游县', '电商县', '光伏县', 
            '养殖县', '种植县', '特色产业县'
        ],
        '政策特征': [
            '东西部协作重点县', '定点帮扶县', '示范县'
        ]
    }
    
    # 措施标签标准化建议
    measure_tag_categories = {
        '产业扶贫': [
            '产业扶贫', '特色产业', '合作社', '龙头企业带动', 
            '土地流转', '职业经理人模式'
        ],
        '基础设施': [
            '基础设施建设', '道路建设', '饮水安全', '电网改造', 
            '网络覆盖', '危房改造'
        ],
        '教育扶贫': [
            '教育扶贫', '教育支持', '雨露计划', '助学补贴', 
            '职业教育', '控辍保学'
        ],
        '医疗扶贫': [
            '医疗保障', '医疗救助', '健康帮扶', '家庭医生', 
            '医保报销'
        ],
        '就业扶贫': [
            '就业帮扶', '技能培训', '劳务输出', '家门口就业', 
            '稳岗补贴'
        ],
        '易地搬迁': [
            '易地搬迁', '集中安置', '搬迁后续扶持'
        ],
        '社会保障': [
            '社会保障', '低保兜底', '特困救助', '养老保险', 
            '临时救助'
        ],
        '金融支持': [
            '金融支持', '小额信贷', '贴息贷款', '金融保险'
        ],
        '组织保障': [
            '驻村帮扶', '第一书记', '帮扶干部', '基层党建', 
            '党组织作用'
        ],
        '机制创新': [
            '精准识别', '动态监测', '督导机制', '问责监督', 
            '干群关系'
        ],
        '协作帮扶': [
            '东西部协作', '定点帮扶', '对口支援', '社会帮扶'
        ],
        '其他': [
            '思想扶贫', '内生动力', '移风易俗', '政策感恩'
        ]
    }
    
    return {
        'county_tags': county_tag_categories,
        'measure_tags': measure_tag_categories
    }


def generate_report(all_data: List[Dict], tag_stats: Dict, standardized: Dict) -> str:
    """生成分析报告"""
    lines = []
    lines.append("=" * 80)
    lines.append("县域标签与措施标签分析报告")
    lines.append("=" * 80)
    lines.append(f"\n总县数: {len(all_data)}")
    
    # 县域标签统计
    lines.append("\n" + "=" * 80)
    lines.append("一、县域标签统计")
    lines.append("=" * 80)
    county_tags = tag_stats['county_tags']['counter']
    lines.append(f"\n共发现 {len(county_tags)} 种不同的县域标签")
    lines.append("\n【标签频次排序（前20）】")
    for tag, count in county_tags.most_common(20):
        lines.append(f"  {tag:30s} : {count:3d} 个县")
    
    # 措施标签统计
    lines.append("\n" + "=" * 80)
    lines.append("二、措施标签统计")
    lines.append("=" * 80)
    measure_tags = tag_stats['measure_tags']['counter']
    lines.append(f"\n共发现 {len(measure_tags)} 种不同的措施标签")
    lines.append("\n【标签频次排序（前30）】")
    for tag, count in measure_tags.most_common(30):
        lines.append(f"  {tag:30s} : {count:3d} 个县")
    
    # 标签模式分析
    lines.append("\n" + "=" * 80)
    lines.append("三、县域标签模式分析")
    lines.append("=" * 80)
    county_patterns = analyze_tag_patterns(county_tags)
    for category, tags_list in county_patterns.items():
        if tags_list:
            lines.append(f"\n【{category}】")
            for tag, count in sorted(tags_list, key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"  {tag:30s} : {count:3d} 个县")
    
    lines.append("\n" + "=" * 80)
    lines.append("四、措施标签模式分析")
    lines.append("=" * 80)
    measure_patterns = analyze_tag_patterns(measure_tags)
    for category, tags_list in measure_patterns.items():
        if tags_list:
            lines.append(f"\n【{category}】")
            for tag, count in sorted(tags_list, key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"  {tag:30s} : {count:3d} 个县")
    
    # 标准化建议
    lines.append("\n" + "=" * 80)
    lines.append("五、标准化标签体系建议")
    lines.append("=" * 80)
    
    lines.append("\n【县域标签标准化体系】")
    for category, tags in standardized['county_tags'].items():
        lines.append(f"\n{category}:")
        for tag in tags:
            lines.append(f"  - {tag}")
    
    lines.append("\n【措施标签标准化体系】")
    for category, tags in standardized['measure_tags'].items():
        lines.append(f"\n{category}:")
        for tag in tags:
            lines.append(f"  - {tag}")
    
    # 问题分析
    lines.append("\n" + "=" * 80)
    lines.append("六、当前标签体系存在的问题")
    lines.append("=" * 80)
    
    # 找出不在标准化体系中的标签
    all_county_tags_set = set(county_tags.keys())
    standardized_county_tags = set()
    for tags in standardized['county_tags'].values():
        standardized_county_tags.update(tags)
    
    unstandardized_county = all_county_tags_set - standardized_county_tags
    if unstandardized_county:
        lines.append("\n【县域标签中未标准化的标签（需要映射）】")
        for tag in sorted(unstandardized_county):
            count = county_tags[tag]
            lines.append(f"  {tag:30s} : {count:3d} 个县")
    
    all_measure_tags_set = set(measure_tags.keys())
    standardized_measure_tags = set()
    for tags in standardized['measure_tags'].values():
        standardized_measure_tags.update(tags)
    
    unstandardized_measure = all_measure_tags_set - standardized_measure_tags
    if unstandardized_measure:
        lines.append("\n【措施标签中未标准化的标签（需要映射）】")
        for tag in sorted(unstandardized_measure):
            count = measure_tags[tag]
            lines.append(f"  {tag:30s} : {count:3d} 个县")
    
    # 建议
    lines.append("\n" + "=" * 80)
    lines.append("七、改进建议")
    lines.append("=" * 80)
    lines.append("""
1. 建立标签映射表：将现有不规范的标签映射到标准化标签
2. 修改提示词：在 county_labeler.py 的 PROMPT_TEMPLATE 中明确指定可用的标签列表
3. 标签数量限制：
   - 县域标签：建议3-6个，固定格式
   - 措施标签：建议4-10个，每个措施必须有标准标签
4. 标签分类：按照建议的12个措施类别进行分类
5. 建立标签验证机制：处理完成后验证标签是否符合标准
    """)
    
    return "\n".join(lines)


def save_tag_mapping(tag_stats: Dict, standardized: Dict, output_file: Path):
    """保存标签映射表（JSON格式）"""
    mapping = {
        'county_tag_mapping': {},
        'measure_tag_mapping': {},
        'standardized_county_tags': standardized['county_tags'],
        'standardized_measure_tags': standardized['measure_tags']
    }
    
    # 生成县域标签映射建议（简单映射：相似度匹配）
    county_tags = tag_stats['county_tags']['counter']
    standardized_county_tags = []
    for tags in standardized['county_tags'].values():
        standardized_county_tags.extend(tags)
    
    for tag in county_tags.keys():
        if tag not in standardized_county_tags:
            # 找到最相似的标准化标签
            best_match = None
            for std_tag in standardized_county_tags:
                if tag in std_tag or std_tag in tag:
                    best_match = std_tag
                    break
            if best_match:
                mapping['county_tag_mapping'][tag] = best_match
    
    # 生成措施标签映射建议
    measure_tags = tag_stats['measure_tags']['counter']
    standardized_measure_tags = []
    for tags in standardized['measure_tags'].values():
        standardized_measure_tags.extend(tags)
    
    for tag in measure_tags.keys():
        if tag not in standardized_measure_tags:
            # 找到最相似的标准化标签
            best_match = None
            for std_tag in standardized_measure_tags:
                if tag in std_tag or std_tag in tag:
                    best_match = std_tag
                    break
            if best_match:
                mapping['measure_tag_mapping'][tag] = best_match
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def main():
    print("🔍 正在加载所有县的标签数据...")
    all_data = load_all_labels()
    print(f"✅ 成功加载 {len(all_data)} 个县的数据")
    
    print("\n📊 正在分析标签...")
    tag_stats = extract_all_tags(all_data)
    
    print("\n💡 正在生成标准化建议...")
    standardized = suggest_standardized_tags(
        tag_stats['county_tags']['counter'],
        tag_stats['measure_tags']['counter']
    )
    
    print("\n📝 正在生成分析报告...")
    report = generate_report(all_data, tag_stats, standardized)
    
    # 保存报告
    report_file = Path(__file__).parent / "output" / "tag_analysis_report.txt"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 分析报告已保存: {report_file}")
    
    # 保存标签映射表
    mapping_file = Path(__file__).parent / "output" / "tag_mapping.json"
    save_tag_mapping(tag_stats, standardized, mapping_file)
    print(f"✅ 标签映射表已保存: {mapping_file}")
    
    # 打印报告摘要
    print("\n" + "=" * 80)
    print("报告摘要")
    print("=" * 80)
    print(report[:2000])  # 打印前2000字符
    print("\n... (完整报告请查看文件)")


if __name__ == "__main__":
    main()

