"""
文本清洗模块
深度清洗访谈文本：去除语气词、口语化转书面语、去重复等
"""

import re
from typing import List, Dict
from config import Config


class TextCleaner:
    """深度文本清洗器"""
    
    def __init__(self):
        self.filler_words = Config.FILLER_WORDS
        self.colloquial_map = Config.COLLOQUIAL_TO_FORMAL
        self.repeat_threshold = Config.REPEAT_THRESHOLD
    
    def remove_filler_words(self, text: str) -> str:
        """
        去除语气词和填充词
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        # 按长度降序排序，避免先替换短的影响长的
        sorted_fillers = sorted(self.filler_words, key=len, reverse=True)
        
        for filler in sorted_fillers:
            # 使用正则，确保独立词（不在词中间）
            # 匹配：句首、逗号后、句号后等位置
            patterns = [
                f'^{re.escape(filler)}[，。,.]?',  # 句首
                f'[，。,.]{re.escape(filler)}[，。,.]?',  # 标点后
                f'{re.escape(filler)}[，。,.]',  # 后接标点
            ]
            
            for pattern in patterns:
                text = re.sub(pattern, '', text)
        
        return text
    
    def colloquial_to_formal(self, text: str) -> str:
        """
        口语化表达转换为书面语
        
        Args:
            text: 原始文本
            
        Returns:
            转换后的文本
        """
        # 按长度降序排序，避免先替换短的影响长的
        sorted_items = sorted(self.colloquial_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for colloquial, formal in sorted_items:
            # 直接替换（中文没有词边界的概念）
            text = text.replace(colloquial, formal)
        
        return text
    
    def remove_repeated_chars(self, text: str) -> str:
        """
        去除重复字符
        例如：哈哈哈哈 → 哈哈
        
        Args:
            text: 原始文本
            
        Returns:
            去重后的文本
        """
        # 连续重复3次以上的字符减少到2次
        def replace_repeat(match):
            char = match.group(1)
            return char * 2
        
        text = re.sub(r'(.)\1{2,}', replace_repeat, text)
        return text
    
    def remove_repeated_phrases(self, text: str) -> str:
        """
        去除重复短语
        例如：我觉得我觉得 → 我觉得
        
        Args:
            text: 原始文本
            
        Returns:
            去重后的文本
        """
        # 检测2-10字的重复短语
        for length in range(10, 1, -1):
            pattern = r'(.{' + str(length) + r'})\1+'
            text = re.sub(pattern, r'\1', text)
        
        return text
    
    def normalize_punctuation(self, text: str) -> str:
        """
        标点符号规范化
        
        Args:
            text: 原始文本
            
        Returns:
            规范化后的文本
        """
        # 全角转半角（英文标点）
        text = text.replace('，', '，')
        text = text.replace('。', '。')
        text = text.replace('！', '！')
        text = text.replace('？', '？')
        text = text.replace('：', '：')
        text = text.replace('；', '；')
        
        # 去除多余空格
        text = re.sub(r'\s+', '', text)
        
        # 去除连续标点
        text = re.sub(r'[，。,.]([，。,.])+', '。', text)
        text = re.sub(r'[！!]+', '！', text)
        text = re.sub(r'[？?]+', '？', text)
        
        # 确保句子以标点结尾
        if text and text[-1] not in '。！？.!?':
            text += '。'
        
        return text
    
    def remove_meaningless_segments(self, text: str) -> str:
        """
        去除无意义片段
        例如：笑声、停顿等
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        meaningless = [
            '笑', '哈哈', '呵呵', '嘿嘿',
            '嗯哼', '唔', '咦', '咳咳',
            '嘶', '哎呀', '哎哟',
        ]
        
        for word in meaningless:
            # 单独出现才删除
            text = re.sub(f'^{re.escape(word)}[，。,.]?', '', text)
            text = re.sub(f'[，。,.]{re.escape(word)}[，。,.]?', '，', text)
        
        return text
    
    def clean_sentence(self, text: str) -> str:
        """
        清洗单句文本（深度清洗）
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        # 1. 去除语气词
        text = self.remove_filler_words(text)
        
        # 2. 去除重复字符
        text = self.remove_repeated_chars(text)
        
        # 3. 去除重复短语
        text = self.remove_repeated_phrases(text)
        
        # 4. 口语化转书面语
        text = self.colloquial_to_formal(text)
        
        # 5. 去除无意义片段
        text = self.remove_meaningless_segments(text)
        
        # 6. 标点符号规范化
        text = self.normalize_punctuation(text)
        
        # 7. 去除首尾空白
        text = text.strip()
        
        return text
    
    def clean_dialogues(self, dialogues: List[Dict]) -> List[Dict]:
        """
        清洗对话列表
        
        Args:
            dialogues: 原始对话列表，格式 [{'speaker': 'Speaker 1', 'text': '...'}]
            
        Returns:
            清洗后的对话列表
        """
        cleaned = []
        
        for item in dialogues:
            speaker = item['speaker']
            text = item['text']
            
            # 清洗文本
            cleaned_text = self.clean_sentence(text)
            
            # 过滤空文本
            if cleaned_text:
                cleaned.append({
                    'speaker': speaker,
                    'text': cleaned_text
                })
        
        return cleaned
    
    def merge_same_speaker(self, dialogues: List[Dict]) -> List[Dict]:
        """
        合并连续的同一说话人对话
        
        Args:
            dialogues: 对话列表
            
        Returns:
            合并后的对话列表
        """
        if not dialogues:
            return []
        
        merged = []
        current_speaker = dialogues[0]['speaker']
        current_text = dialogues[0]['text']
        
        for item in dialogues[1:]:
            if item['speaker'] == current_speaker:
                # 同一说话人，合并文本
                current_text += item['text']
            else:
                # 不同说话人，保存上一段
                merged.append({
                    'speaker': current_speaker,
                    'text': current_text
                })
                current_speaker = item['speaker']
                current_text = item['text']
        
        # 保存最后一段
        merged.append({
            'speaker': current_speaker,
            'text': current_text
        })
        
        return merged
    
    def format_to_text(self, dialogues: List[Dict], 
                       show_speaker: bool = True,
                       speaker_labels: Dict[str, str] = None) -> str:
        """
        格式化为纯文本
        
        Args:
            dialogues: 对话列表
            show_speaker: 是否显示说话人标记
            speaker_labels: 说话人标签映射，如 {'Speaker 1': '访谈者', 'Speaker 2': '受访者'}
            
        Returns:
            格式化后的文本
        """
        lines = []
        
        for item in dialogues:
            speaker = item['speaker']
            text = item['text']
            
            # 应用自定义标签
            if speaker_labels and speaker in speaker_labels:
                speaker = speaker_labels[speaker]
            
            if show_speaker:
                lines.append(f"{speaker}：{text}")
            else:
                lines.append(text)
        
        return '\n\n'.join(lines)

