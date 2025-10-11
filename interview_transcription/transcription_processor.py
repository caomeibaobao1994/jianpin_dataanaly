"""
转写处理器
整合多种后端API和文本清洗，提供完整的处理流程
"""

import json
from pathlib import Path
from typing import Optional, Dict
from text_cleaner import TextCleaner
from config import Config


class TranscriptionProcessor:
    """访谈转写处理器（支持多后端）"""
    
    def __init__(self, backend: str = None):
        """
        初始化处理器
        
        Args:
            backend: 后端选择 ('iflytek' 或 'whisperx')，None则使用配置默认值
        """
        self.backend = backend or Config.DEFAULT_BACKEND
        self.transcriber = None
        self.cleaner = TextCleaner()
        self.output_dir = Config.setup_output_dir()
        
        # 延迟加载转写器（避免导入错误）
        self._load_transcriber()
    
    def _load_transcriber(self):
        """加载对应的转写器"""
        if self.backend == 'iflytek':
            from iflytek_api import IFlytekTranscriber
            self.transcriber = IFlytekTranscriber()
            print(f"🔧 使用后端: 讯飞语音转写")
        
        elif self.backend == 'whisperx':
            from whisperx_api import WhisperXTranscriber
            self.transcriber = WhisperXTranscriber(
                model_size=Config.WHISPERX_MODEL,
                device=Config.WHISPERX_DEVICE,
                compute_type=Config.WHISPERX_COMPUTE_TYPE,
                hf_token=Config.HF_TOKEN
            )
            print(f"🔧 使用后端: WhisperX (模型: {Config.WHISPERX_MODEL})")
        
        else:
            raise ValueError(f"未知的后端: {self.backend}")
    
    def validate_audio_file(self, audio_path: Path) -> bool:
        """
        验证音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            是否有效
        """
        # 检查文件是否存在
        if not audio_path.exists():
            print(f"❌ 文件不存在: {audio_path}")
            return False
        
        # 检查文件格式
        if audio_path.suffix.lower() not in Config.SUPPORTED_FORMATS:
            print(f"❌ 不支持的格式: {audio_path.suffix}")
            print(f"   支持的格式: {', '.join(Config.SUPPORTED_FORMATS)}")
            return False
        
        # 检查文件大小
        file_size = audio_path.stat().st_size
        if file_size > Config.MAX_FILE_SIZE:
            print(f"❌ 文件过大: {file_size / 1024 / 1024:.2f}MB")
            print(f"   最大支持: {Config.MAX_FILE_SIZE / 1024 / 1024}MB")
            return False
        
        if file_size == 0:
            print(f"❌ 文件为空: {audio_path}")
            return False
        
        return True
    
    def process_single_file(self, 
                          audio_path: str,
                          speaker_labels: Dict[str, str] = None,
                          output_name: str = None) -> bool:
        """
        处理单个音频文件
        
        Args:
            audio_path: 音频文件路径
            speaker_labels: 说话人标签，如 {'Speaker 1': '访谈者', 'Speaker 2': '受访者'}
            output_name: 输出文件名（不含扩展名），默认使用音频文件名
            
        Returns:
            是否处理成功
        """
        audio_path = Path(audio_path)
        
        print(f"\n{'='*60}")
        print(f"🎤 处理音频: {audio_path.name}")
        print(f"{'='*60}\n")
        
        # 1. 验证文件
        if not self.validate_audio_file(audio_path):
            return False
        
        # 2. 调用讯飞API转写
        print("\n【步骤1】调用讯飞API进行语音转写...")
        dialogues = self.transcriber.transcribe(audio_path)
        
        if not dialogues:
            print("❌ 转写失败")
            return False
        
        print(f"✅ 转写成功，共获得{len(dialogues)}段对话")
        
        # 3. 保存原始文本（可选）
        if Config.SAVE_RAW_TEXT:
            print("\n【步骤2】保存原始转写文本...")
            raw_text = self.cleaner.format_to_text(dialogues, speaker_labels=speaker_labels)
            raw_file = self._save_text(
                raw_text,
                audio_path.stem if not output_name else output_name,
                suffix='_raw'
            )
            print(f"✅ 原始文本已保存: {raw_file}")
        
        # 4. 深度清洗文本
        print("\n【步骤3】深度清洗文本...")
        print("   - 去除语气词和填充词")
        print("   - 口语化转书面语")
        print("   - 去除重复字符和短语")
        print("   - 规范化标点符号")
        
        cleaned_dialogues = self.cleaner.clean_dialogues(dialogues)
        merged_dialogues = self.cleaner.merge_same_speaker(cleaned_dialogues)
        
        print(f"✅ 清洗完成，合并后共{len(merged_dialogues)}段对话")
        
        # 5. 保存清洗后文本
        if Config.SAVE_CLEANED_TEXT:
            print("\n【步骤4】保存清洗后文本...")
            cleaned_text = self.cleaner.format_to_text(
                merged_dialogues,
                speaker_labels=speaker_labels
            )
            cleaned_file = self._save_text(
                cleaned_text,
                audio_path.stem if not output_name else output_name,
                suffix='_cleaned'
            )
            print(f"✅ 清洗文本已保存: {cleaned_file}")
        
        # 6. 保存JSON格式（可选）
        if Config.SAVE_JSON:
            print("\n【步骤5】保存JSON格式...")
            json_file = self._save_json(
                merged_dialogues,
                audio_path.stem if not output_name else output_name
            )
            print(f"✅ JSON文件已保存: {json_file}")
        
        print(f"\n{'='*60}")
        print(f"✅ 处理完成: {audio_path.name}")
        print(f"{'='*60}\n")
        
        return True
    
    def process_batch(self, audio_dir: str, speaker_labels: Dict[str, str] = None):
        """
        批量处理音频文件
        
        Args:
            audio_dir: 音频文件目录
            speaker_labels: 说话人标签
        """
        audio_dir = Path(audio_dir)
        
        if not audio_dir.exists():
            print(f"❌ 目录不存在: {audio_dir}")
            return
        
        # 查找所有音频文件
        audio_files = []
        for ext in Config.SUPPORTED_FORMATS:
            audio_files.extend(audio_dir.glob(f"*{ext}"))
        
        if not audio_files:
            print(f"❌ 未找到音频文件（支持格式: {', '.join(Config.SUPPORTED_FORMATS)}）")
            return
        
        print(f"\n🎯 找到 {len(audio_files)} 个音频文件")
        print(f"   使用后端: {self.backend}")
        print(f"{'='*60}\n")
        
        success_count = 0
        fail_count = 0
        
        for idx, audio_file in enumerate(audio_files, 1):
            print(f"\n进度: {idx}/{len(audio_files)}")
            
            if self.process_single_file(audio_file, speaker_labels):
                success_count += 1
            else:
                fail_count += 1
        
        # 打印汇总
        print(f"\n{'='*60}")
        print(f"📊 批量处理完成")
        print(f"   后端: {self.backend}")
        print(f"   成功: {success_count} 个")
        print(f"   失败: {fail_count} 个")
        print(f"{'='*60}\n")
    
    def _save_text(self, text: str, base_name: str, suffix: str = '') -> Path:
        """
        保存文本文件
        
        Args:
            text: 文本内容
            base_name: 基础文件名
            suffix: 文件名后缀
            
        Returns:
            保存的文件路径
        """
        output_file = self.output_dir / f"{base_name}{suffix}.txt"
        output_file.write_text(text, encoding='utf-8')
        return output_file
    
    def _save_json(self, dialogues: list, base_name: str) -> Path:
        """
        保存JSON文件
        
        Args:
            dialogues: 对话列表
            base_name: 基础文件名
            
        Returns:
            保存的文件路径
        """
        output_file = self.output_dir / f"{base_name}.json"
        
        data = {
            'total_segments': len(dialogues),
            'dialogues': dialogues
        }
        
        output_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        return output_file

