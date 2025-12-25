import os
import re
import json

def extract_county_from_filename(filename):
    """
    从访谈文件名中提取县/镇名称。
    假定县/镇信息通常出现在“访谈”和“村”或“脱贫户”之间。
    """
    match = re.search(r'访谈(.+?)(村|脱贫户)', filename)
    if match:
        return match.group(1).strip()
    return "未知县镇"

def analyze_counties(summary_dir):
    """
    遍历指定目录下的减贫措施分析JSON文件，提取县名和分析结果。
    """
    county_data = {}
    for filename in os.listdir(summary_dir):
        if filename.endswith("_poverty_summary.json"):
            filepath = os.path.join(summary_dir, filename)
            county_name = extract_county_from_filename(filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if county_name not in county_data:
                    county_data[county_name] = {
                        "summaries": [],
                        "measures": {},
                        "key_highlights": [],
                        "living_changes": []
                    }
                
                county_data[county_name]["summaries"].append(data.get("summary", ""))
                
                for dimension, measures_list in data.get("measures", {}).items():
                    if isinstance(measures_list, list):
                        if dimension not in county_data[county_name]["measures"]:
                            county_data[county_name]["measures"][dimension] = []
                        for measure in measures_list:
                            if measure != "未提及" and measure not in county_data[county_name]["measures"][dimension]:
                                county_data[county_name]["measures"][dimension].append(measure)
                
                for highlight in data.get("key_highlights", []):
                    if highlight not in county_data[county_name]["key_highlights"]:
                        county_data[county_name]["key_highlights"].append(highlight)
                
                county_data[county_name]["living_changes"].append(data.get("living_changes", ""))
                
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filepath}: {e}")
            except Exception as e:
                print(f"Error processing file {filepath}: {e}")
                
    return county_data

if __name__ == "__main__":
    summary_directory = "/Users/sunwenbo/Documents/RUC/github/jianpin_dataanaly/output/4_poverty_reduction_summary/"
    
    # 打印测试结果，验证县名提取
    test_filename = "250810 应用经济学院本科生蒋予凡访谈田村镇湖塘村脱贫户刘七香-压缩_poverty_summary.json"
    extracted_county = extract_county_from_filename(test_filename)
    print(f"测试文件名: {test_filename} -> 提取的县/镇: {extracted_county}")
    
    # 运行分析并打印汇总数据（仅作验证，实际报告生成会更详细）
    all_county_data = analyze_counties(summary_directory)
    print("\n--- 县级汇总数据 ---")
    for county, data in all_county_data.items():
        print(f"县/镇: {county}")
        print(f"  访谈数量: {len(data['summaries'])}")
        print(f"  主要减贫措施维度: {list(data['measures'].keys())}")
        print(f"  亮点数量: {len(data['key_highlights'])}")
        print(f"  生活变化总结数量: {len(data['living_changes'])}")
        print("-" * 30)


