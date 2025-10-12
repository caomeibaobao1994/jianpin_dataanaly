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
        去除语气词和填充词（保留标点符号）
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        # 按长度降序排序，避免先替换短的影响长的
        sorted_fillers = sorted(self.filler_words, key=len, reverse=True)
        
        for filler in sorted_fillers:
            escaped_filler = re.escape(filler)
            
            # 1. 句首的语气词（后面可能有标点）- 保留标点
            # "啊，你好" → "，你好"  "嗯。" → "。"
            text = re.sub(f'^{escaped_filler}([，。,.！？!?]?)', r'\1', text)
            
            # 2. 标点后的语气词后面又跟标点 - 合并标点（避免重复标点）
            # "你好，啊，我是" → "你好，我是"
            text = re.sub(f'([，。,.！？!?]){escaped_filler}[，。,.！？!?]', r'\1', text)
            
            # 3. 语气词后接标点（保留标点）
            # "你好啊，我是" → "你好，我是"
            text = re.sub(f'{escaped_filler}([，。,.！？!?])', r'\1', text)
            
            # 4. 孤立的语气词（前后都不是标点和空格）
            # "你好啊我是" → "你好我是"
            text = re.sub(f'(?<=[^，。,.！？!?\s]){escaped_filler}(?=[^，。,.！？!?\s])', '', text)
        
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
    
    def parse_speaker_text(self, text: str) -> List[Dict]:
        """
        解析带说话人标记的文本，转换为对话列表
        
        支持的格式：
        - 【访谈者】文本内容
        - 访谈者：文本内容
        
        Args:
            text: 带说话人标记的文本字符串
            
        Returns:
            对话列表 [{'speaker': '访谈者', 'text': '...'}]
        """
        dialogues = []
        
        # 匹配【说话人】或说话人：格式
        # 支持：【访谈者】文本 或 访谈者：文本
        pattern = r'(?:【([^】]+)】|([^：\n]+)：)([^\n【]+)'
        
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            speaker = match.group(1) or match.group(2)  # 【】内或：前的内容
            content = match.group(3)  # 文本内容
            
            if speaker and content:
                speaker = speaker.strip()
                content = content.strip()
                
                if content:  # 过滤空文本
                    dialogues.append({
                        'speaker': speaker,
                        'text': content
                    })
        
        return dialogues
    
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
                lines.append(f"【{speaker}】{text}")
            else:
                lines.append(text)
        
        return '\n\n'.join(lines)
    
    def clean_transcript(self, text: str, merge_speakers: bool = True, 
                        deep_clean: bool = True, use_ai: bool = False,
                        ai_batch_size: int = 5) -> str:
        """
        清洗转写文本（统一入口）
        
        处理流程：
        1. 解析带说话人标记的文本
        2. 合并连续同一说话人的段落（可选）
        3. 深度文本清洗（可选）
        4. AI智能优化（可选，需要智谱AI API）
        5. 格式化输出
        
        Args:
            text: 原始转写文本（带说话人标记）
            merge_speakers: 是否合并连续同一说话人
            deep_clean: 是否进行规则深度清洗
            use_ai: 是否使用智谱AI进行智能优化
            ai_batch_size: AI处理时每批次的段落数
            
        Returns:
            清洗后的文本
        """
        # 1. 解析文本
        dialogues = self.parse_speaker_text(text)
        
        if not dialogues:
            return text  # 解析失败，返回原文
        
        # 2. 合并连续同一说话人（如果需要）
        if merge_speakers:
            dialogues = self.merge_same_speaker(dialogues)
        
        # 3. 规则深度清洗（如果需要）
        if deep_clean:
            dialogues = self.clean_dialogues(dialogues)
        
        # 4. AI智能优化（如果需要）
        if use_ai:
            try:
                from zhipu_cleaner import ZhipuTextCleaner
                print("\n🤖 启用智谱AI智能优化...")
                ai_cleaner = ZhipuTextCleaner()
                dialogues = ai_cleaner.clean_dialogue_batch(dialogues, batch_size=ai_batch_size)
            except ImportError as e:
                print(f"⚠️  无法使用智谱AI: {str(e)}")
                print("   请安装: pip install zhipuai")
            except Exception as e:
                print(f"⚠️  AI清洗出错: {str(e)}")
                print("   将继续使用规则清洗结果")
        
        # 5. 格式化输出
        return self.format_to_text(dialogues, show_speaker=True)

