#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为 input_text 下的每个县生成基础信息文本（使用高德地图API）

功能：
- 遍历 interview_transcription/input_text 下的一级子目录（视为一个县）
- 调用高德地理编码接口获取：省/市、经纬度、区划级别
- 调用高德地点搜索接口（可选）获取产业相关关键词（产业园/工业园/特色产业）
- 生成基础信息文件，默认写到县目录下的 “基础信息.txt”

使用前提：
- 在环境变量或 config.py 中提供 AMAP_KEY（高德Web服务Key）
  export AMAP_KEY=你的高德key

示例：
    python fetch_county_briefs.py
    python fetch_county_briefs.py --root input_text --limit 5 --overwrite
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from config import Config


AMAP_KEY = os.getenv("AMAP_KEY") or os.getenv("GAODE_KEY")
DEFAULT_ROOT = Path(__file__).parent / "input_text"
OUTPUT_FILENAME = "基础信息.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
}


class AmapClient:
    """高德API简单封装，仅用到地理编码与文本搜索。"""

    def __init__(self, key: str):
        if not key:
            raise ValueError("未找到高德Key，请设置环境变量 AMAP_KEY 或 GAODE_KEY")
        self.key = key

    def geocode(self, address: str) -> Optional[Dict]:
        url = "https://restapi.amap.com/v3/geocode/geo"
        params = {"key": self.key, "address": address, "batch": "false"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1" or not data.get("geocodes"):
            return None
        return data["geocodes"][0]

    def search_industry(self, keyword: str, city: Optional[str]) -> List[Dict]:
        """文本搜索产业相关POI，返回前若干条。"""
        url = "https://restapi.amap.com/v5/place/text"
        params = {
            "key": self.key,
            "keywords": keyword,
            "region": city or "",
            "types": "",
            "page_size": 10,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            return []
        return data.get("pois", []) or []


def extract_pure_county_name(full_name: str) -> str:
    """
    从完整县名中提取纯县名（去掉省、市、自治区等前缀）。
    例如："河北省巨鹿县" -> "巨鹿县"，"西藏自治区林芝市工布江达县" -> "工布江达县"
    """
    name = full_name.strip()
    
    # 先去掉括号及其内容（如"（贵州省六盘水市）"、"（20250116-0117）"）
    name = re.sub(r'[（(].*?[）)]', '', name).strip()
    
    # 去掉数字和短横前缀（如"0716-0717河北省巨鹿县"、"1河北省石家庄市平山县"）
    # 使用正则表达式匹配开头的数字、短横、下划线、空格
    name = re.sub(r'^[\d\s\-_]+', '', name).strip()
    
    # 去掉常见的行政区划前缀
    prefixes = [
        "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省", "江苏省", "浙江省", "安徽省",
        "福建省", "江西省", "山东省", "河南省", "湖北省", "湖南省", "广东省", "海南省",
        "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省", "台湾省",
        "内蒙古自治区", "广西壮族自治区", "西藏自治区", "宁夏回族自治区", "新疆维吾尔自治区",
        "北京市", "天津市", "上海市", "重庆市",
        "香港特别行政区", "澳门特别行政区",
    ]
    
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):].strip()
            break
    
    # 如果还有"市"前缀（如"邢台市巨鹿县"、"石家庄市平山县"），也去掉
    if name.startswith("市"):
        name = name[1:].strip()
    elif "市" in name:
        # 找到最后一个"市"的位置
        idx = name.rindex("市")
        if idx < len(name) - 1:  # 如果"市"后面还有内容（如"石家庄市平山县"）
            name = name[idx + 1:].strip()
        # 如果"市"在末尾（如"文山市"），不需要处理，保留原样
    
    # 如果还有"自治州"或"州"前缀（如"红河哈尼族彝族自治州屏边县"），也去掉
    if "自治州" in name:
        idx = name.rindex("自治州")
        if idx < len(name) - 3:  # 确保"自治州"后面还有内容
            name = name[idx + 3:].strip()
    elif "州" in name and not name.endswith("州"):
        # 找到最后一个"州"的位置，去掉"州"及其前面的内容
        # 例如："红河州屏边县" -> "屏边县"
        idx = name.rindex("州")
        if idx < len(name) - 1:  # 确保"州"后面还有内容
            name = name[idx + 1:].strip()
    
    # 确保以"县"、"市"、"区"、"旗"等结尾
    if not any(name.endswith(suffix) for suffix in ["县", "市", "区", "旗", "自治县", "自治旗"]):
        # 如果去掉前缀后没有合适的后缀，尝试从原名称中提取
        for suffix in ["县", "市", "区", "旗", "自治县", "自治旗"]:
            if suffix in full_name:
                idx = full_name.rindex(suffix)
                name = full_name[idx - 10:idx + len(suffix)]  # 取后缀前10个字符
                break
    
    # 如果名称仍然包含城市名（如"娄底新化县"），直接提取最后一个"县"、"区"等后缀及其前面的部分
    # 这样"娄底新化县" -> "新化县"，"河北省石家庄市平山县" -> "平山县"
    suffixes = ["自治县", "自治旗", "县", "市", "区", "旗"]  # 先匹配长的，再匹配短的
    original_name = name  # 保存原始名称用于比较
    for suffix in suffixes:
        # 只有当名称长度>4时才提取（避免"井冈山市"、"麻栗坡县"等4个字符的正确名称被错误提取）
        if name.endswith(suffix) and len(name) > 4:
            # 如果名称以"县"等结尾，但长度超过"XX县"（3个字符），可能是"城市名+县名"的格式
            # 提取最后3-5个字符（通常是县名，如"新化县"、"麻栗坡县"、"井冈山市"）
            # 对于"市"，通常提取3个字符；对于"县"，可能是3-4个字符
            if suffix == "市":
                # "市"通常提取3个字符（如"文山市"、"涟源市"）
                try_lengths = [3, 4, 5]
            else:
                # "县"等可能是3-4个字符（如"新化县"、"麻栗坡县"）
                try_lengths = [4, 3, 5]
            
            for length in try_lengths:
                if len(name) >= length:
                    potential_name = name[-length:]
                    # 确保提取的部分以合适的后缀结尾，且比原名称短
                    if any(potential_name.endswith(s) for s in suffixes) and len(potential_name) < len(name):
                        name = potential_name
                        break
            if len(name) < len(original_name):  # 如果已经提取到更短的名称，跳出循环
                break
        elif suffix in name and not name.endswith(suffix):
            # 如果名称包含后缀但不以它结尾，找到最后一个后缀的位置
            idx = name.rindex(suffix)
            # 提取后缀及其前面的部分（最多4个字符，通常是县名）
            potential_name = name[max(0, idx - 4):idx + len(suffix)]
            # 如果提取的部分以合适的后缀结尾，使用它
            if any(potential_name.endswith(s) for s in suffixes):
                name = potential_name
                break
    
    return name if name else full_name


def fetch_baike_info(county_name: str) -> Tuple[str, Dict[str, str]]:
    """
    抓取百度百科简介及基础要点（如面积/人口/气候等）。
    返回: (summary, key_facts_dict)
    """
    # 提取纯县名（去掉省、市前缀）
    pure_name = extract_pure_county_name(county_name)
    
    # 先尝试用纯县名（URL编码）
    url = f"https://baike.baidu.com/item/{quote(pure_name)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        # 检查是否成功（不是重定向到搜索页）
        if "item" in resp.url:
            pass  # 成功
        else:
            # 如果重定向，尝试用完整名称
            url = f"https://baike.baidu.com/item/{quote(county_name)}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
    except Exception:
        # 如果纯县名失败，尝试完整名称
        try:
            url = f"https://baike.baidu.com/item/{quote(county_name)}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except Exception:
            return "", {}

    soup = BeautifulSoup(resp.text, "lxml")

    # 简介 - 尝试多种可能的class名称（适配新旧版本）
    summary = ""
    # 新版本：lemmaSummary_iFCrC, summary_xM7FA
    for class_name in ["lemma-summary", "lemmaSummary_iFCrC", "summary_xM7FA", "J-summary"]:
        summary_div = soup.find("div", class_=lambda x: x and class_name in str(x))
        if summary_div:
            text = summary_div.get_text(separator=" ", strip=True)
            summary = clean_baike_text(text)
            if summary and len(summary) > 50:  # 确保有实际内容
                break
    
    # 如果还没找到，尝试查找所有包含summary的div
    if not summary or len(summary) < 50:
        for div in soup.find_all("div", class_=lambda x: x and "summary" in str(x).lower()):
            text = div.get_text(separator=" ", strip=True)
            cleaned = clean_baike_text(text)
            if cleaned and len(cleaned) > 50 and "巨鹿" in cleaned:  # 确保包含县名
                summary = cleaned
                break
    
    # 备用方案：使用meta description
    if not summary or len(summary) < 50:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            summary = clean_baike_text(meta_desc["content"])
    
    # 最后备用：查找第一个有意义的p标签
    if not summary or len(summary) < 50:
        for p in soup.find_all("p"):
            text = p.get_text(separator=" ", strip=True)
            cleaned = clean_baike_text(text)
            # 跳过版权信息
            if cleaned and len(cleaned) > 50 and not any(k in cleaned for k in ["百度", "必读", "协议", "隐私", "ICP"]):
                summary = cleaned
                break

    # 基本信息表 - 尝试多种可能的class名称和结构
    key_facts: Dict[str, str] = {}
    
    # 方法1: 查找 basic-info 或 basicInfo（适配新旧版本）
    for class_name in ["basic-info", "basicInfo", "basic-info cmn-clearfix", "basic-info J-basic-info", 
                       "basicInfo_M3XoO", "J-basic-info"]:
        basic_info = soup.find("div", class_=lambda x: x and class_name in str(x))
        if basic_info:
            # 尝试dt/dd结构
            names = basic_info.find_all("dt")
            values = basic_info.find_all("dd")
            if names and values:
                for dt_tag, dd_tag in zip(names, values):
                    key = dt_tag.get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                    val = dd_tag.get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                    if key and val and len(key) < 50 and len(val) < 200:
                        key_facts[key] = clean_baike_text(val, max_len=120)
                if key_facts:
                    break
            
            # 尝试新的结构：infoName___ccB 和 infoDesc_wB1R2
            info_names = basic_info.find_all("div", class_=lambda x: x and "infoName" in str(x))
            info_descs = basic_info.find_all("div", class_=lambda x: x and "infoDesc" in str(x))
            if info_names and info_descs:
                for name_div, desc_div in zip(info_names, info_descs):
                    key = name_div.get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                    val = desc_div.get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                    if key and val and len(key) < 50 and len(val) < 200:
                        key_facts[key] = clean_baike_text(val, max_len=120)
                if key_facts:
                    break
    
    # 方法2: 如果方法1失败，尝试查找所有dt/dd对（可能在dl标签中）
    if not key_facts:
        for dl in soup.find_all("dl", class_=lambda x: x and ("basic" in x.lower() or "info" in x.lower())):
            names = dl.find_all("dt")
            values = dl.find_all("dd")
            for dt_tag, dd_tag in zip(names, values):
                key = dt_tag.get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                val = dd_tag.get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                if key and val and len(key) < 50 and len(val) < 200:
                    key_facts[key] = clean_baike_text(val, max_len=120)
    
    # 方法3: 尝试从表格中提取（table标签）
    if not key_facts:
        for table in soup.find_all("table", class_=lambda x: x and ("basic" in str(x).lower() or "info" in str(x).lower())):
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    key = cells[0].get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                    val = cells[1].get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                    if key and val and len(key) < 50 and len(val) < 200:
                        key_facts[key] = clean_baike_text(val, max_len=120)
    
    # 方法4: 从所有dt/dd对中提取（更宽泛的搜索）
    if not key_facts:
        all_dts = soup.find_all("dt")
        all_dds = soup.find_all("dd")
        # 尝试匹配相邻的dt和dd
        for dt in all_dts:
            dd = dt.find_next_sibling("dd")
            if dd:
                key = dt.get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                val = dd.get_text(separator=" ", strip=True).replace("\xa0", " ").strip()
                if key and val and len(key) < 50 and len(val) < 200:
                    key_facts[key] = clean_baike_text(val, max_len=120)
    
    # 方法5: 从basicInfo_M3XoO的纯文本中解析（新版本百度百科）
    if not key_facts:
        basic_info_div = soup.find("div", class_=lambda x: x and "basicInfo" in str(x) and "J-basic-info" in str(x))
        if basic_info_div:
            full_text = basic_info_div.get_text(separator=" ", strip=True)
            # 尝试解析类似"中文名巨鹿县外文名Julu County"这样的格式
            # 常见字段模式
            patterns = [
                (r"中文名\s*([^\s外别行]+)", "中文名"),
                (r"外文名\s*([^\s别行]+)", "外文名"),
                (r"别\s*名\s*([^\s行]+)", "别名"),
                (r"行政区划代码\s*([^\s行]+)", "行政区划代码"),
                (r"行政区类别\s*([^\s所]+)", "行政区类别"),
                (r"所属地区\s*([^\s地]+)", "所属地区"),
                (r"地理位置\s*([^\s面]+)", "地理位置"),
                (r"面\s*积\s*([^\s下]+)", "面积"),
                (r"下辖地区\s*([^\s政]+)", "下辖地区"),
                (r"政府驻地\s*([^\s电]+)", "政府驻地"),
                (r"电话区号\s*([^\s邮]+)", "电话区号"),
                (r"邮政编码\s*([^\s气]+)", "邮政编码"),
                (r"气候条件\s*([^\s人]+)", "气候条件"),
                (r"人口数量\s*([^\s火]+)", "人口数量"),
                (r"火车站\s*([^\s车]+)", "火车站"),
                (r"车牌代码\s*([^\s地]+)", "车牌代码"),
                (r"地区生产总值\s*([^\s]+)", "地区生产总值"),
            ]
            for pattern, label in patterns:
                match = re.search(pattern, full_text)
                if match:
                    value = match.group(1).strip()
                    if value and len(value) < 200:
                        key_facts[label] = clean_baike_text(value, max_len=120)

    # 只保留常见要点（放宽匹配条件）
    whitelist = [
        "行政区划代码", "代码", "面积", "人口", "总人口", "常住人口", "户籍人口",
        "方言", "气候", "气候类型", "气候条件", "邮政", "邮政区码", "邮编",
        "车牌", "车牌代码", "海拔", "政府", "政府驻地", "驻地", "行政中心",
        "地理位置", "位置", "坐标", "经纬度", "GDP", "生产总值", "经济",
        "产业", "主要产业", "特色产业", "农业", "工业", "服务业"
    ]
    filtered = {}
    for k, v in key_facts.items():
        # 如果键包含白名单关键词，或者值看起来像是有用的信息
        if any(w in k for w in whitelist) or (len(v) > 5 and len(v) < 100):
            filtered[k] = v

    return summary, filtered


def clean_baike_text(text: str, max_len: int = 1000) -> str:
    """去除百科版权/协议等噪声，截断到合理长度。"""
    noise_keywords = [
        "百度百科合作平台",
        "使用百度前必读",
        "隐私政策",
        "百科协议",
        "©",
        "ICP",
    ]
    lines = text.splitlines()
    cleaned: List[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(k in line for k in noise_keywords):
            continue
        cleaned.append(line)
    result = " ".join(cleaned)
    result = " ".join(result.split())  # 压缩多余空格
    if len(result) > max_len:
        result = result[:max_len].rstrip() + "…"
    return result


def extract_industry_keywords(pois: List[Dict]) -> List[str]:
    """从POI列表提取行业/业态关键词。"""
    results: List[str] = []
    for poi in pois:
        name = poi.get("name")
        typecode = poi.get("typecode", "")
        typename = poi.get("type", "")
        if name:
            results.append(name)
        elif typename:
            results.append(typename)
        elif typecode:
            results.append(typecode)
        if len(results) >= 8:
            break
    # 去重保持顺序
    seen = set()
    dedup = []
    for item in results:
        if item not in seen:
            seen.add(item)
            dedup.append(item)
    return dedup


def build_brief_text(
    county_name: str,
    geocode: Optional[Dict],
    industry_keywords: List[str],
    data_source: str,
    baike_summary: str = "",
    baike_key_facts: Optional[Dict[str, str]] = None,
) -> str:
    today = dt.date.today().isoformat()
    province = geocode.get("province") if geocode else "未提及"
    city = geocode.get("city") if geocode else "未提及"
    district = geocode.get("district") if geocode else county_name
    level = geocode.get("level") if geocode else "未提及"
    location = geocode.get("location") if geocode else "未提及"
    formatted_address = geocode.get("formatted_address") if geocode else "未提及"

    industry_block = "、".join(industry_keywords) if industry_keywords else "未提及"
    baike_block = baike_summary.strip() if baike_summary else "未提及（百科/官网抓取失败或为空）"
    baike_facts_block = "；".join([f"{k}: {v}" for k, v in (baike_key_facts or {}).items()]) if baike_key_facts else "未提及"

    lines = [
        f"县名：{county_name}",
        f"行政归属：{province} / {city} / {district}",
        f"地理位置：{formatted_address}",
        f"经纬度：{location}",
        f"区划级别：{level}",
        f"区位交通：未提及（需手动补充或另行查询）",
        f"主导产业/园区关键词：{industry_block}",
        f"资源禀赋：未提及（需手动补充或另行查询）",
        f"人口与城镇化：未提及（需手动补充或另行查询）",
        f"近期发展关键词：未提及（需手动补充或另行查询）",
        f"百科/官网简介：{baike_block}",
        f"百科要点：{baike_facts_block}",
        f"数据来源：{data_source}",
        f"数据时间：{today}",
    ]
    return "\n".join(lines)


def derive_county_name(dir_path: Path) -> str:
    """从目录名去掉日期/编号前缀的一个简单启发式。"""
    name = dir_path.name
    # 去掉前缀的数字和短横，如 "0714-0715河北省平乡县" -> "河北省平乡县"
    while name and (name[0].isdigit() or name[0] in {"-", "_"}):
        name = name[1:]
    return name or dir_path.name


def process_county(
    county_dir: Path,
    client: AmapClient,
    overwrite: bool = False,
) -> Tuple[bool, str]:
    """处理单个县目录，返回(成功标志, 信息)。"""
    output_file = county_dir / OUTPUT_FILENAME
    if output_file.exists() and not overwrite:
        return False, f"已存在，跳过：{output_file}"

    county_name = derive_county_name(county_dir)
    geocode = client.geocode(county_name)

    city = None
    if geocode:
        city = geocode.get("city") or geocode.get("province")

    pois = []
    try:
        pois = client.search_industry(f"{county_name} 产业园", city)
        if not pois:
            pois = client.search_industry(f"{county_name} 工业园", city)
    except Exception:
        pois = []

    industry_keywords = extract_industry_keywords(pois)
    baike_summary, baike_key_facts = fetch_baike_info(county_name)

    text = build_brief_text(
        county_name=county_name,
        geocode=geocode,
        industry_keywords=industry_keywords,
        data_source="高德地理编码/POI检索",
        baike_summary=baike_summary,
        baike_key_facts=baike_key_facts,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)

    return True, f"已生成：{output_file}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量生成县域基础信息（高德API）")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="input_text 根目录")
    parser.add_argument("--limit", type=int, default=0, help="仅处理前N个县目录，0表示全量")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有的基础信息文件")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"目录不存在: {root}")

    client = AmapClient(AMAP_KEY or getattr(Config, "AMAP_KEY", ""))

    county_dirs = [p for p in root.iterdir() if p.is_dir()]
    county_dirs.sort()
    if args.limit and args.limit > 0:
        county_dirs = county_dirs[: args.limit]

    total = len(county_dirs)
    print(f"待处理县目录数：{total}")

    done = 0
    for i, county_dir in enumerate(county_dirs, 1):
        try:
            created, info = process_county(county_dir, client, overwrite=args.overwrite)
            prefix = "✅" if created else "⏭️"
            print(f"[{i}/{total}] {prefix} {info}")
            if created:
                done += 1
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[{i}/{total}] ❌ 失败：{county_dir.name} - {exc}")

    print(f"完成：新生成 {done} 个，合计目录 {total}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"❌ 运行失败：{exc}", file=sys.stderr)
        sys.exit(1)

