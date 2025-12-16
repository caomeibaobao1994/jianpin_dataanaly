#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证标签是否符合标准化体系
"""

import json
from pathlib import Path
from typing import Dict, List, Set

OUTPUT_DIR = Path(__file__).parent / "output" / "4_poverty_reduction_summary"

# 标准化的县域标签
STANDARD_COUNTY_TAGS = {
    # 地形特征（必选1个）
    "地形特征": {"山区县", "高原县", "平原县", "丘陵县", "盆地县", "河谷县"},
    # 区位特征（可选0-2个）
    "区位特征": {"革命老区县", "民族聚居县", "边境县", "易地搬迁重点县", "生态脆弱区", "资源型县"},
    # 产业特征（可选0-2个）
    "产业特征": {"农业大县", "特色产业县", "旅游县", "电商县", "光伏县", "养殖县", "种植县"},
    # 政策特征（可选0-1个）
    "政策特征": {"东西部协作重点县", "定点帮扶县", "示范县"},
}

# 标准化的措施标签
STANDARD_MEASURE_TAGS = {
    "产业扶贫": {"产业扶贫", "特色产业", "合作社", "龙头企业带动", "土地流转", "职业经理人模式"},
    "基础设施": {"基础设施建设", "道路建设", "饮水安全", "电网改造", "网络覆盖", "危房改造"},
    "教育扶贫": {"教育扶贫", "教育支持", "雨露计划", "助学补贴", "职业教育", "控辍保学"},
    "医疗扶贫": {"医疗保障", "医疗救助", "健康帮扶", "家庭医生", "医保报销"},
    "就业扶贫": {"就业帮扶", "技能培训", "劳务输出", "家门口就业", "稳岗补贴"},
    "易地搬迁": {"易地搬迁", "集中安置", "搬迁后续扶持"},
    "社会保障": {"社会保障", "低保兜底", "特困救助", "养老保险", "临时救助"},
    "金融支持": {"金融支持", "小额信贷", "贴息贷款", "金融保险"},
    "组织保障": {"驻村帮扶", "第一书记", "帮扶干部", "基层党建", "党组织作用"},
    "机制创新": {"精准识别", "动态监测", "督导机制", "问责监督", "干群关系"},
    "协作帮扶": {"东西部协作", "定点帮扶", "对口支援", "社会帮扶"},
    "其他": {"思想扶贫", "内生动力", "移风易俗", "政策感恩"},
}

# 所有标准标签的集合
ALL_STANDARD_COUNTY_TAGS = set()
for tags in STANDARD_COUNTY_TAGS.values():
    ALL_STANDARD_COUNTY_TAGS.update(tags)

ALL_STANDARD_MEASURE_TAGS = set()
for tags in STANDARD_MEASURE_TAGS.values():
    ALL_STANDARD_MEASURE_TAGS.update(tags)


def validate_county_tags(county_tags: List[str]) -> Dict[str, any]:
    """验证县域标签"""
    errors = []
    warnings = []
    
    # 检查数量
    if len(county_tags) < 3:
        errors.append(f"县域标签数量不足：{len(county_tags)}个（要求3-6个）")
    elif len(county_tags) > 6:
        errors.append(f"县域标签数量过多：{len(county_tags)}个（要求3-6个）")
    
    # 检查是否包含地形特征标签
    terrain_tags = STANDARD_COUNTY_TAGS["地形特征"]
    has_terrain = any(tag in terrain_tags for tag in county_tags)
    if not has_terrain:
        errors.append("缺少必选的地形特征标签")
    
    # 检查非标准标签
    non_standard = [tag for tag in county_tags if tag not in ALL_STANDARD_COUNTY_TAGS]
    if non_standard:
        warnings.append(f"发现非标准标签：{', '.join(non_standard)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_measure_tags(measures: List[Dict]) -> Dict[str, any]:
    """验证措施标签"""
    errors = []
    warnings = []
    
    # 检查数量
    if len(measures) < 4:
        errors.append(f"措施标签数量不足：{len(measures)}个（要求4-10个）")
    elif len(measures) > 10:
        errors.append(f"措施标签数量过多：{len(measures)}个（要求4-10个）")
    
    # 检查每个措施的标签和佐证
    non_standard_tags = []
    missing_evidence = []
    
    for i, measure in enumerate(measures):
        if not isinstance(measure, dict):
            errors.append(f"措施{i+1}格式错误：不是字典格式")
            continue
        
        tag = measure.get("tag", "")
        evidence = measure.get("evidence", "")
        
        if not tag:
            errors.append(f"措施{i+1}缺少标签")
        
        if tag and tag not in ALL_STANDARD_MEASURE_TAGS:
            non_standard_tags.append(tag)
        
        if not evidence or evidence.strip() == "":
            missing_evidence.append(f"措施{i+1}({tag})")
        elif len(evidence) > 60:
            warnings.append(f"措施{i+1}({tag})的佐证过长：{len(evidence)}字（建议<=60字）")
    
    if non_standard_tags:
        warnings.append(f"发现非标准措施标签：{', '.join(non_standard_tags)}")
    
    if missing_evidence:
        errors.append(f"以下措施缺少佐证：{', '.join(missing_evidence)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_file(file_path: Path) -> Dict[str, any]:
    """验证单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        county_name = data.get("county_name", "未知")
        county_tags = data.get("county_tags", [])
        effective_measures = data.get("effective_measures", [])
        
        county_validation = validate_county_tags(county_tags)
        measure_validation = validate_measure_tags(effective_measures)
        
        return {
            "county_name": county_name,
            "file": file_path.name,
            "county_tags": county_validation,
            "measures": measure_validation,
            "overall_valid": county_validation["valid"] and measure_validation["valid"]
        }
    except Exception as e:
        return {
            "county_name": "未知",
            "file": file_path.name,
            "error": str(e),
            "overall_valid": False
        }


def main():
    """主函数"""
    print("🔍 正在验证所有标签文件...")
    
    label_files = list(OUTPUT_DIR.glob("*_labels.json"))
    total = len(label_files)
    
    results = []
    valid_count = 0
    invalid_count = 0
    
    for file_path in label_files:
        result = validate_file(file_path)
        results.append(result)
        if result.get("overall_valid", False):
            valid_count += 1
        else:
            invalid_count += 1
    
    # 打印报告
    print(f"\n{'='*80}")
    print("标签验证报告")
    print(f"{'='*80}")
    print(f"\n总文件数: {total}")
    print(f"✅ 完全符合标准: {valid_count}")
    print(f"❌ 存在问题: {invalid_count}")
    
    # 详细报告
    print(f"\n{'='*80}")
    print("详细验证结果（仅显示有问题的文件）")
    print(f"{'='*80}")
    
    for result in results:
        if not result.get("overall_valid", False):
            print(f"\n【{result['county_name']}】")
            print(f"文件: {result['file']}")
            
            if "error" in result:
                print(f"  ❌ 读取错误: {result['error']}")
                continue
            
            # 县域标签问题
            if not result["county_tags"]["valid"]:
                print("  县域标签问题:")
                for err in result["county_tags"]["errors"]:
                    print(f"    ❌ {err}")
                for warn in result["county_tags"]["warnings"]:
                    print(f"    ⚠️  {warn}")
            
            # 措施标签问题
            if not result["measures"]["valid"]:
                print("  措施标签问题:")
                for err in result["measures"]["errors"]:
                    print(f"    ❌ {err}")
                for warn in result["measures"]["warnings"]:
                    print(f"    ⚠️  {warn}")
    
    # 统计非标准标签
    print(f"\n{'='*80}")
    print("非标准标签统计")
    print(f"{'='*80}")
    
    non_standard_county_tags = {}
    non_standard_measure_tags = {}
    
    for result in results:
        if "error" in result:
            continue
        
        county_name = result["county_name"]
        
        # 统计非标准县域标签
        for tag in result.get("county_tags", {}).get("warnings", []):
            if "非标准标签" in tag:
                # 提取标签名
                import re
                matches = re.findall(r'：(.+)', tag)
                if matches:
                    tags = matches[0].split('、')
                    for t in tags:
                        t = t.strip()
                        if t not in non_standard_county_tags:
                            non_standard_county_tags[t] = []
                        non_standard_county_tags[t].append(county_name)
        
        # 统计非标准措施标签
        for tag in result.get("measures", {}).get("warnings", []):
            if "非标准措施标签" in tag:
                import re
                matches = re.findall(r'：(.+)', tag)
                if matches:
                    tags = matches[0].split('、')
                    for t in tags:
                        t = t.strip()
                        if t not in non_standard_measure_tags:
                            non_standard_measure_tags[t] = []
                        non_standard_measure_tags[t].append(county_name)
    
    if non_standard_county_tags:
        print("\n【非标准县域标签】")
        for tag, counties in sorted(non_standard_county_tags.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {tag:30s} : {len(counties):3d} 个县")
    
    if non_standard_measure_tags:
        print("\n【非标准措施标签】")
        for tag, counties in sorted(non_standard_measure_tags.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
            print(f"  {tag:30s} : {len(counties):3d} 个县")
    
    # 保存验证结果
    report_file = OUTPUT_DIR.parent / "tag_validation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": total,
                "valid": valid_count,
                "invalid": invalid_count
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 详细验证结果已保存: {report_file}")


if __name__ == "__main__":
    main()

