#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
县域标签与减贫措施提炼工具（基于智谱AI）

功能：
- 读取某个县的基础信息与多份访谈文本，自动生成：
  1) 县域标签（地理/区位/产业/历史等特征）
  2) 脱贫有效措施标签（具体做法 + 简短佐证）
  3) 2-3 句总结
- 仅对单个县运行，方便先验校验输出效果

用法示例：
    python county_labeler.py \
        --county-dir "/Users/sunwenbo/Documents/RUC/github/jianpin_dataanaly/interview_transcription/input_text/河北省张家口市蔚县 （20240722-20240723）" \
        --text-dir "/Users/sunwenbo/Documents/RUC/github/jianpin_dataanaly/interview_transcription/input_text/河北省张家口市蔚县 （20240722-20240723）/河北省张家口市蔚县 （20240722-20240723）文本"

参数说明：
- county-dir  : 县目录，需包含《基础信息.txt》
- text-dir    : 访谈文本所在目录（docx/txt，可递归）
- combined-file: 若已合并好的访谈汇总文本，可直接传入跳过合并
- output      : 可选，结果输出路径，默认写入 output/4_poverty_reduction_summary/{县名}_labels.json
- char-limit: 限制传给模型的访谈文本字符数（默认 50000），超长文本采用"开头+结尾"策略截断
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from zhipuai import ZhipuAI

from config import Config
from county_text_merger import merge_county_texts


PROMPT_TEMPLATE = """你是一名县域脱贫与乡村振兴分析专家。
任务：结合县域基础信息与多份访谈文本，提炼“县域标签”和“脱贫有效措施标签”，为政策研究提供快速画像。

【县域基础信息】
{county_context}

【访谈文本（多份合并，如文本过长已截断，会显示"中间省略"提示）】
{interview_text}

【输出要求】

1. 县域标签（必须3-6个，必须从以下标准标签中选择，不允许自定义）：
   - 地形特征（必选1个）：山区县、高原县、平原县、丘陵县、盆地县、河谷县
   - 区位特征（可选0-2个）：革命老区县、民族聚居县、边境县、易地搬迁重点县、生态脆弱区、资源型县
   - 产业特征（可选0-2个）：农业大县、特色产业县、旅游县、电商县、光伏县、养殖县、种植县
   - 政策特征（可选0-1个）：东西部协作重点县、定点帮扶县、示范县

2. 脱贫有效措施标签（必须4-10个，必须从以下标准标签中选择，不允许自定义）：
   - 产业扶贫：产业扶贫、特色产业、合作社、龙头企业带动、土地流转、职业经理人模式
   - 基础设施：基础设施建设、道路建设、饮水安全、电网改造、网络覆盖、危房改造
   - 教育扶贫：教育扶贫、教育支持、雨露计划、助学补贴、职业教育、控辍保学
   - 医疗扶贫：医疗保障、医疗救助、健康帮扶、家庭医生、医保报销
   - 就业扶贫：就业帮扶、技能培训、劳务输出、家门口就业、稳岗补贴
   - 易地搬迁：易地搬迁、集中安置、搬迁后续扶持
   - 社会保障：社会保障、低保兜底、特困救助、养老保险、临时救助
   - 金融支持：金融支持、小额信贷、贴息贷款、金融保险
   - 组织保障：驻村帮扶、第一书记、帮扶干部、基层党建、党组织作用
   - 机制创新：精准识别、动态监测、督导机制、问责监督、干群关系
   - 协作帮扶：东西部协作、定点帮扶、对口支援、社会帮扶
   - 其他：思想扶贫、内生动力、移风易俗、政策感恩

   每条措施需给出<=60字的具体佐证，必须来源于上述文本或明确标注"未提及"。

3. 总结：2-3 句话，概括该县有效的减贫模式；如信息不足需说明。

【重要约束】
- 所有标签必须严格从上述标准列表中选择，不允许使用列表外的标签
- 如果文本中提到的内容没有对应标准标签，选择最接近的标准标签
- 县域标签必须包含1个地形特征标签
- 措施标签的佐证必须具体、真实，来源于文本内容

【输出JSON，严格JSON格式，无markdown】
{{
  "county_name": "{county_name}",
  "county_tags": ["标签1", "标签2", "..."],
  "effective_measures": [
    {{"tag": "措施标签", "evidence": "来自访谈/基础信息的简短佐证"}}
  ],
  "summary": "2-3句总结，如信息缺失需说明"
}}
"""


class CountyLabeler:
    """基于智谱AI的县域标签与减贫措施提炼器。"""

    def __init__(
        self,
        api_key: str = Config.ZHIPU_API_KEY,
        model: str = Config.ZHIPU_MODEL,
        base_url: Optional[str] = getattr(Config, "ZHIPU_BASE_URL", None),
    ) -> None:
        if not api_key:
            raise ValueError("缺少 ZHIPU_API_KEY，请在 config.py 或环境变量中配置")
        self.client = ZhipuAI(api_key=api_key, base_url=base_url) if base_url else ZhipuAI(api_key=api_key)
        self.model = model

    def _build_prompt(self, county_name: str, county_context: str, interview_text: str) -> str:
        """组装提示词。"""
        context_block = county_context.strip() if county_context.strip() else "（基础信息缺失）"
        interview_block = interview_text.strip() if interview_text.strip() else "（访谈文本缺失）"
        return PROMPT_TEMPLATE.format(
            county_name=county_name,
            county_context=context_block,
            interview_text=interview_block,
        )

    def analyze(self, county_name: str, county_context: str, interview_text: str) -> Dict:
        """调用智谱模型生成标签与总结。"""
        prompt = self._build_prompt(county_name, county_context, interview_text)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        
        # 移除markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # 尝试解析JSON，如果失败则尝试修复
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # 保存原始响应到文件以便调试
            debug_file = Path(__file__).parent / "output" / f"json_error_{county_name.replace('/', '_')}.txt"
            debug_file.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"错误位置: {e.pos}\n")
                f.write(f"错误信息: {e}\n\n")
                f.write("="*80 + "\n")
                f.write("原始内容:\n")
                f.write(content)
            
            print(f"⚠️  JSON解析失败，已保存调试信息到: {debug_file}")
            print(f"   错误位置: {e.pos}, 错误: {e.msg}")
            
            # 策略1: 尝试修复未闭合的字符串
            fixed_content = self._fix_json_strings(content, e.pos)
            try:
                return json.loads(fixed_content)
            except json.JSONDecodeError as e2:
                print(f"   修复策略1失败: {e2.msg}")
            
            # 策略2: 提取JSON部分（查找第一个{到最后一个}）
            json_start = content.find('{')
            json_end = content.rfind('}')
            if json_start >= 0 and json_end > json_start:
                json_part = content[json_start:json_end+1]
                try:
                    return json.loads(json_part)
                except json.JSONDecodeError as e3:
                    print(f"   提取JSON部分失败: {e3.msg}")
            
            # 策略3: 使用更宽松的解析（尝试修复常见的转义问题）
            try:
                # 转义所有未转义的换行符（在字符串值中）
                import re
                # 匹配 "key": "value" 中的value部分
                def escape_newlines(match):
                    key = match.group(1)
                    value = match.group(2)
                    # 转义换行符，但保留已转义的
                    value = re.sub(r'(?<!\\)\n', '\\n', value)
                    value = re.sub(r'(?<!\\)\r', '\\r', value)
                    return f'{key}: "{value}"'
                
                pattern = r'("(?:evidence|summary|county_name)"\s*:\s*")([^"]*(?:"[^"]*"[^"]*)*)"'
                relaxed_content = re.sub(pattern, escape_newlines, content)
                return json.loads(relaxed_content)
            except (json.JSONDecodeError, Exception) as e4:
                print(f"   宽松解析失败: {e4}")
            
            # 最后策略：返回基本结构，包含错误信息
            print(f"❌ 所有修复策略失败，返回基本结构")
            return {
                "county_name": county_name,
                "county_tags": [],
                "effective_measures": [],
                "summary": f"JSON解析失败: {e.msg} (位置: {e.pos})",
                "error": str(e),
                "error_position": e.pos,
                "raw_content_length": len(content),
                "debug_file": str(debug_file)
            }
    
    def _fix_json_strings(self, content: str, error_pos: int) -> str:
        """尝试修复JSON字符串问题"""
        import re
        
        # 策略1: 转义字符串值中的未转义换行符和引号
        # 查找所有 "key": "value" 模式，修复value中的问题
        def fix_string_value(match):
            key_part = match.group(1)
            value_part = match.group(2)
            # 转义未转义的换行符、回车符和引号
            value_part = value_part.replace('\n', '\\n').replace('\r', '\\r')
            value_part = value_part.replace('"', '\\"') if value_part.count('"') % 2 == 1 else value_part
            return f'{key_part}: "{value_part}"'
        
        # 修复 evidence 字段中的字符串（最常见的问题）
        pattern = r'("evidence"\s*:\s*")([^"]*(?:"[^"]*"[^"]*)*)"'
        content = re.sub(pattern, fix_string_value, content, flags=re.MULTILINE)
        
        # 策略2: 如果还有问题，尝试在错误位置附近添加闭合引号
        if error_pos < len(content):
            # 在错误位置前查找最后一个未闭合的引号
            before_error = content[:error_pos]
            quote_count = before_error.count('"') - before_error.count('\\"')
            if quote_count % 2 == 1:
                # 有未闭合的引号，尝试在错误位置前添加闭合引号
                insert_pos = error_pos
                while insert_pos > 0 and content[insert_pos-1] not in ['"', '\n']:
                    insert_pos -= 1
                if insert_pos > 0:
                    content = content[:insert_pos] + '"' + content[insert_pos:]
        
        return content


def load_base_info(county_dir: Path) -> str:
    """读取县目录下的基础信息文本。"""
    base_file = county_dir / "基础信息.txt"
    if not base_file.exists():
        raise FileNotFoundError(f"未找到基础信息文件：{base_file}")
    return base_file.read_text(encoding="utf-8", errors="ignore").strip()


def ensure_combined_text(text_dir: Path, output_file: Path) -> Path:
    """合并访谈 docx/txt 为单一文本文件，若已存在则复用。"""
    if output_file.exists():
        return output_file
    merge_county_texts(text_dir, output_file)
    return output_file


def load_interview_text(combined_file: Path, char_limit: int) -> str:
    """
    读取访谈汇总文本并做智能截断。
    
    策略：
    1. 如果文本长度 <= char_limit，直接返回全文
    2. 如果超过，采用"开头+结尾"策略，各取约 char_limit/2，优先在段落边界截断
    """
    text = combined_file.read_text(encoding="utf-8", errors="ignore").strip()
    total_len = len(text)
    
    if total_len <= char_limit:
        return text
    
    # 超长文本，采用"开头+结尾"策略
    half_limit = char_limit // 2
    prefix = text[:half_limit]
    suffix_start = total_len - half_limit
    suffix = text[suffix_start:]
    
    # 尝试在段落边界截断（查找最后一个换行符）
    last_newline_pos = prefix.rfind('\n')
    if last_newline_pos > half_limit * 0.8:  # 如果换行符位置不太靠前
        prefix = text[:last_newline_pos]
    
    first_newline_pos = suffix.find('\n')
    if first_newline_pos > 0 and first_newline_pos < half_limit * 0.2:  # 如果换行符位置不太靠后
        suffix = suffix[first_newline_pos + 1:]
    
    omitted_chars = total_len - len(prefix) - len(suffix)
    return f"{prefix}\n\n[... 中间省略约 {omitted_chars} 字符 ...]\n\n{suffix}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="县域标签与减贫措施提炼（单县版，智谱AI）")
    parser.add_argument("--county-dir", required=True, help="县目录路径，需包含基础信息.txt")
    parser.add_argument("--text-dir", help="访谈文本目录（docx/txt，可递归）")
    parser.add_argument("--combined-file", help="已合并好的访谈汇总文件，传入后跳过合并")
    parser.add_argument(
        "--output",
        help="结果输出路径，默认 output/4_poverty_reduction_summary/{县名}_labels.json",
    )
    parser.add_argument(
        "--char-limit",
        type=int,
        default=50000,
        help="访谈文本传给模型的最大字符数（默认50000），超长文本采用'开头+结尾'策略智能截断",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    county_dir = Path(args.county_dir).expanduser().resolve()
    if not county_dir.exists():
        raise FileNotFoundError(f"县目录不存在：{county_dir}")

    county_name = county_dir.name
    county_context = load_base_info(county_dir)

    # 处理访谈文本
    if args.combined_file:
        combined_path = Path(args.combined_file).expanduser().resolve()
    else:
        text_dir = Path(args.text_dir).expanduser().resolve() if args.text_dir else None
        if not text_dir or not text_dir.exists():
            raise FileNotFoundError("请通过 --text-dir 指定访谈文本目录，或提供 --combined-file")
        default_output = Path(__file__).parent / "output" / "2_merged_texts" / f"{text_dir.name}_combined.txt"
        combined_path = ensure_combined_text(text_dir, default_output)

    interview_text = load_interview_text(combined_path, args.char_limit)

    analyzer = CountyLabeler()
    result = analyzer.analyze(county_name=county_name, county_context=county_context, interview_text=interview_text)

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_dir = Path(__file__).parent / "output" / "4_poverty_reduction_summary"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{county_name}_labels.json"

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 分析完成，已保存：{output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"❌ 运行失败：{exc}", file=sys.stderr)
        sys.exit(1)

