#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
减贫措施分析器
基于智谱AI对访谈内容进行分析，提取和总结减贫措施
"""

import json
from typing import Dict, List
from zhipuai import ZhipuAI
from config import Config


class PovertyReductionAnalyzer:
    """减贫措施智能分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.api_key = Config.ZHIPU_API_KEY
        self.model = Config.ZHIPU_MODEL
        self.base_url = Config.ZHIPU_BASE_URL
        self.client = ZhipuAI(api_key=self.api_key, base_url=self.base_url)
        
        if not self.api_key:
            raise ValueError("智谱AI API密钥未设置，请在config.py或.env中配置ZHIPU_API_KEY")
        
        # 定义减贫措施的分析维度
        self.dimensions = [
            "住房保障",
            "教育支持", 
            "医疗保障",
            "就业帮扶",
            "产业扶贫",
            "基础设施建设",
            "社会保障",
            "帮扶干部工作",
            "其他措施"
        ]
    
    def _build_analysis_prompt(self, interview_text: str) -> str:
        """
        构建分析提示词
        
        Args:
            interview_text: 访谈文本内容
            
        Returns:
            分析提示词
        """
        prompt = f"""你是一位专业的扶贫政策分析专家。请仔细阅读以下访谈内容，从中提取和总结该地区在脱贫攻坚过程中实施的具体减贫措施。

【访谈内容】
{interview_text}

【分析要求】
请按照以下维度进行分析和提取，如果某个维度在访谈中没有提及，可以标注为"未提及"：

1. **住房保障**：建房、改造、搬迁等住房相关措施
2. **教育支持**：子女教育、助学金、教育资助等
3. **医疗保障**：医疗救助、健康帮扶等
4. **就业帮扶**：外出务工、技能培训、就业推荐等
5. **产业扶贫**：发展产业、种植养殖、合作社等
6. **基础设施建设**：道路、水电、网络等基础设施改善
7. **社会保障**：低保、养老、救助金等
8. **帮扶干部工作**：驻村干部、第一书记的具体帮扶工作
9. **其他措施**：上述维度之外的其他减贫措施

【输出格式】
请以JSON格式输出，包含以下字段：
{{
  "summary": "整体减贫措施概述（2-3句话）",
  "measures": {{
    "住房保障": ["具体措施1", "具体措施2", ...],
    "教育支持": ["具体措施1", "具体措施2", ...],
    "医疗保障": ["未提及"] 或 ["具体措施"],
    ...
  }},
  "key_highlights": ["亮点1", "亮点2", "亮点3"],
  "living_changes": "受访者生活变化的简要描述"
}}

请确保：
1. 提取的措施要具体、真实，来源于访谈内容
2. 不要臆造访谈中没有的信息
3. 用简洁的语言描述每个措施
4. 输出严格的JSON格式，不要添加额外说明文字
"""
        return prompt
    
    def analyze_interview(self, interview_text: str) -> Dict:
        """
        分析访谈内容，提取减贫措施
        
        Args:
            interview_text: 访谈文本内容
            
        Returns:
            分析结果字典
        """
        print("🔍 正在分析访谈内容，提取减贫措施...")
        
        try:
            # 构建提示词
            prompt = self._build_analysis_prompt(interview_text)
            
            # 调用智谱AI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 较低温度确保输出稳定
            )
            
            # 获取响应内容
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            # 移除可能的markdown代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # 解析JSON
            result = json.loads(content)
            
            print("✅ 减贫措施分析完成")
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON解析失败: {e}")
            print(f"原始响应: {content[:500]}...")
            # 返回一个基本结构
            return {
                "summary": "分析失败，无法解析AI响应",
                "measures": {},
                "key_highlights": [],
                "living_changes": "",
                "error": str(e)
            }
        except Exception as e:
            print(f"❌ 减贫措施分析失败: {e}")
            return {
                "summary": "分析过程出错",
                "measures": {},
                "key_highlights": [],
                "living_changes": "",
                "error": str(e)
            }
    
    def format_analysis_result(self, analysis_result: Dict, audio_filename: str = "") -> str:
        """
        格式化分析结果为可读文本
        
        Args:
            analysis_result: 分析结果字典
            audio_filename: 音频文件名
            
        Returns:
            格式化的文本报告
        """
        lines = []
        
        # 标题
        if audio_filename:
            lines.append(f"访谈文件：{audio_filename}")
            lines.append("="*80)
        
        # 整体概述
        lines.append("\n📋 【减贫措施整体概述】")
        lines.append(analysis_result.get("summary", "无"))
        
        # 生活变化
        if analysis_result.get("living_changes"):
            lines.append("\n👥 【受访者生活变化】")
            lines.append(analysis_result.get("living_changes", ""))
        
        # 具体措施（按维度）
        lines.append("\n📊 【具体减贫措施】")
        measures = analysis_result.get("measures", {})
        
        for dimension in self.dimensions:
            if dimension in measures:
                items = measures[dimension]
                
                # 处理字符串类型（如"未提及"）
                if isinstance(items, str):
                    if items != "未提及":
                        lines.append(f"\n{dimension}：")
                        lines.append(f"  • {items}")
                # 处理列表类型
                elif isinstance(items, list) and items and items != ["未提及"]:
                    lines.append(f"\n{dimension}：")
                    for item in items:
                        lines.append(f"  • {item}")
        
        # 亮点总结
        highlights = analysis_result.get("key_highlights", [])
        if highlights:
            lines.append("\n⭐ 【工作亮点】")
            for i, highlight in enumerate(highlights, 1):
                lines.append(f"  {i}. {highlight}")
        
        # 错误信息（如果有）
        if "error" in analysis_result:
            lines.append(f"\n⚠️  分析过程中出现错误：{analysis_result['error']}")
        
        return "\n".join(lines)
    
    def save_analysis(self, analysis_result: Dict, output_file: str, audio_filename: str = ""):
        """
        保存分析结果到文件
        
        Args:
            analysis_result: 分析结果字典
            output_file: 输出文件路径
            audio_filename: 音频文件名
        """
        # 保存为可读文本
        formatted_text = self.format_analysis_result(analysis_result, audio_filename)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        # 同时保存JSON格式（便于后续数据分析）
        json_file = output_file.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 分析报告已保存: {output_file}")
        print(f"   ✅ JSON数据已保存: {json_file}")


if __name__ == "__main__":
    """测试减贫措施分析功能"""
    
    # 读取测试文件
    test_file = "output/3_ai_optimized/10月11日_ai.txt"
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取访谈内容（跳过前面的元信息）
        lines = content.split('\n')
        interview_start = 0
        for i, line in enumerate(lines):
            if '=' * 20 in line:
                interview_start = i + 1
                break
        interview_text = '\n'.join(lines[interview_start:])
        
        # 创建分析器
        analyzer = PovertyReductionAnalyzer()
        
        # 分析访谈
        result = analyzer.analyze_interview(interview_text)
        
        # 输出结果
        print("\n" + "="*80)
        print(analyzer.format_analysis_result(result, "10月11日.MP3"))
        print("="*80)
        
        # 保存结果
        analyzer.save_analysis(result, "output/test_减贫措施分析.txt", "10月11日.MP3")
        
    except FileNotFoundError:
        print(f"❌ 测试文件不存在: {test_file}")
        print("   请先运行批处理生成访谈文本")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

