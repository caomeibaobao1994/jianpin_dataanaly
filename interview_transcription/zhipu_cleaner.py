#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱AI文本清洗模块
使用智谱AI的大语言模型进行访谈文本的智能优化
"""

import json
import time
from typing import List, Dict, Optional
from config import Config

try:
    from zhipuai import ZhipuAI
    ZHIPU_AVAILABLE = True
except ImportError:
    ZHIPU_AVAILABLE = False
    print("⚠️  提示：未安装zhipuai库，请运行: pip install zhipuai")


class ZhipuTextCleaner:
    """基于智谱AI的智能文本清洗器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化智谱AI客户端
        
        Args:
            api_key: 智谱AI API密钥，默认从Config读取
        """
        if not ZHIPU_AVAILABLE:
            raise ImportError("未安装zhipuai库，请运行: pip install zhipuai")
        
        self.api_key = api_key or Config.ZHIPU_API_KEY
        self.model = Config.ZHIPU_MODEL
        self.client = ZhipuAI(api_key=self.api_key)
        
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一位专业的访谈文本编辑专家，擅长将口语化的访谈录音转写稿优化为清晰、规范的书面文本。

你的任务：
1. 保留访谈的原意和所有关键信息，不要删减任何重要内容
2. 去除口语化的语气词（如：嗯、啊、呃、那个、这个、就是等），但保持自然流畅
3. 修正语法错误和不通顺的表达，使其更加规范
4. 适当调整句子结构，使逻辑更清晰
5. 保留【说话人】标记格式
6. 保持原有的段落结构（不要合并不同说话人的内容）
7. 对于重复啰嗦的表达，可适当精简，但不改变原意

注意事项：
- 不要添加原文中没有的内容
- 保持访谈的真实性和自然感
- 标点符号要规范使用
- 确保每个说话人的段落都以【说话人】开头"""

    def _build_user_prompt(self, text: str) -> str:
        """构建用户提示词"""
        return f"""请优化以下访谈转写文本：

{text}

请直接输出优化后的文本，不要添加任何解释说明。"""

    def clean_text(self, text: str, temperature: float = 0.3, 
                   max_retries: int = 3) -> Optional[str]:
        """
        使用智谱AI清洗文本
        
        Args:
            text: 原始文本
            temperature: 模型温度参数（0-1），越低越保守
            max_retries: 最大重试次数
            
        Returns:
            清洗后的文本，失败返回None
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(text)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=4000,
                )
                
                cleaned_text = response.choices[0].message.content.strip()
                return cleaned_text
                
            except Exception as e:
                print(f"⚠️  API调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    print("❌ 达到最大重试次数，清洗失败")
                    return None
    
    def clean_dialogue_batch(self, dialogues: List[Dict], 
                            batch_size: int = 5) -> List[Dict]:
        """
        批量清洗对话列表（分批处理，避免token超限）
        
        Args:
            dialogues: 对话列表 [{'speaker': '访谈者', 'text': '...'}]
            batch_size: 每批处理的对话数量
            
        Returns:
            清洗后的对话列表
        """
        cleaned_dialogues = []
        total = len(dialogues)
        
        print(f"\n🤖 开始使用智谱AI清洗文本（共{total}个段落）...")
        
        for i in range(0, total, batch_size):
            batch = dialogues[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"   处理批次 {batch_num}/{total_batches} ({len(batch)}个段落)...")
            
            # 将批次转换为文本
            batch_text = self._dialogues_to_text(batch)
            
            # 调用AI清洗
            cleaned_text = self.clean_text(batch_text)
            
            if cleaned_text:
                # 解析清洗后的文本
                cleaned_batch = self._text_to_dialogues(cleaned_text)
                cleaned_dialogues.extend(cleaned_batch)
            else:
                # 清洗失败，使用原文
                print(f"   ⚠️  批次 {batch_num} 清洗失败，保留原文")
                cleaned_dialogues.extend(batch)
            
            # 避免请求过快
            if i + batch_size < total:
                time.sleep(1)
        
        print(f"✅ 智谱AI清洗完成！")
        return cleaned_dialogues
    
    def _dialogues_to_text(self, dialogues: List[Dict]) -> str:
        """将对话列表转换为文本"""
        lines = []
        for item in dialogues:
            speaker = item['speaker']
            text = item['text']
            lines.append(f"【{speaker}】{text}")
        return '\n\n'.join(lines)
    
    def _text_to_dialogues(self, text: str) -> List[Dict]:
        """将文本解析回对话列表"""
        import re
        dialogues = []
        
        # 匹配【说话人】格式
        pattern = r'【([^】]+)】([^【]+)'
        matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            speaker = match.group(1).strip()
            content = match.group(2).strip()
            
            if speaker and content:
                dialogues.append({
                    'speaker': speaker,
                    'text': content
                })
        
        return dialogues


def test_zhipu_cleaner():
    """测试智谱AI清洗功能"""
    if not ZHIPU_AVAILABLE:
        print("❌ 请先安装zhipuai库: pip install zhipuai")
        return
    
    # 测试文本
    test_text = """【访谈者】比起来，然后比起来，然后您的生活哪些变化？就像您刚刚说的，比如说造房子呀，比如说你家小孩读书啊这些有哪些变化让您比较印象深刻？

【受访者】怎么说呢我都说不上来，就是那个嗯。

【访谈者】哪些感觉生活是不是哪些地方变好了，嗯？"""

    print("="*60)
    print("测试智谱AI文本清洗")
    print("="*60)
    print("\n原始文本：")
    print(test_text)
    
    try:
        cleaner = ZhipuTextCleaner()
        cleaned = cleaner.clean_text(test_text)
        
        print("\n" + "="*60)
        print("清洗后文本：")
        print("="*60)
        print(cleaned)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")


if __name__ == '__main__':
    test_zhipu_cleaner()

