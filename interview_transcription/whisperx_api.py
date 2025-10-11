# -*- coding: utf-8 -*-
"""
WhisperX API 封装
使用 WhisperX 进行语音转写和说话人分离
官方仓库: https://github.com/m-bain/whisperX
"""

import os
from pathlib import Path
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')


class WhisperXTranscriber:
    """WhisperX 语音转写客户端（支持说话人分离）"""
    
    def __init__(self, 
                 model_size: str = "small",
                 device: str = "cpu",
                 compute_type: str = "int8",
                 hf_token: str = None):
        """
        初始化 WhisperX 转写客户端
        
        Args:
            model_size: 模型大小 (tiny/base/small/medium/large)
            device: 设备 (cpu/cuda)
            compute_type: 计算精度 (int8/float16/float32)
            hf_token: Hugging Face Token（说话人分离需要）
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.hf_token = hf_token
        
        self.model = None
        self.align_model = None
        self.diarize_model = None
        
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖是否已安装"""
        try:
            import whisperx
            self.whisperx = whisperx
        except ImportError:
            raise ImportError(
                "WhisperX 未安装。请运行:\n"
                "pip3 install git+https://github.com/m-bain/whisperX.git"
            )
        
        try:
            import torch
        except ImportError:
            raise ImportError(
                "PyTorch 未安装。请运行:\n"
                "pip3 install torch"
            )
    
    def load_models(self):
        """加载模型"""
        if self.model is None:
            print(f"📥 正在加载 Whisper 模型: {self.model_size}")
            print("   首次使用会自动下载模型，请耐心等待...")
            
            self.model = self.whisperx.load_model(
                self.model_size,
                self.device,
                compute_type=self.compute_type,
                language="zh"
            )
            print("✅ Whisper 模型加载完成")
    
    def load_align_model(self, language_code="zh"):
        """加载对齐模型"""
        if self.align_model is None:
            print("📥 正在加载时间对齐模型...")
            self.align_model, self.align_metadata = self.whisperx.load_align_model(
                language_code=language_code,
                device=self.device
            )
            print("✅ 对齐模型加载完成")
    
    def load_diarize_model(self):
        """加载说话人分离模型"""
        if self.diarize_model is None:
            if not self.hf_token:
                raise ValueError(
                    "说话人分离需要 Hugging Face Token。\n"
                    "请访问 https://huggingface.co/settings/tokens 获取。"
                )
            
            print("📥 正在加载说话人分离模型...")
            print("   首次使用会自动下载模型，请耐心等待...")
            
            self.diarize_model = self.whisperx.DiarizationPipeline(
                use_auth_token=self.hf_token,
                device=self.device
            )
            print("✅ 说话人分离模型加载完成")
    
    def transcribe_audio(self, audio_path: Path) -> Optional[Dict]:
        """
        转写音频
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转写结果字典
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 加载模型
        self.load_models()
        
        # 加载音频
        print(f"📄 正在加载音频: {audio_path.name}")
        audio = self.whisperx.load_audio(str(audio_path))
        
        # 转写
        print("🎤 正在进行语音转写...")
        result = self.model.transcribe(audio, batch_size=16)
        
        print(f"✅ 转写完成，共识别出 {len(result['segments'])} 个片段")
        
        return result
    
    def align_timestamps(self, audio_path: Path, result: Dict) -> Dict:
        """
        优化时间戳对齐
        
        Args:
            audio_path: 音频文件路径
            result: 转写结果
            
        Returns:
            对齐后的结果
        """
        self.load_align_model()
        
        print("⏱️  正在优化时间戳对齐...")
        audio = self.whisperx.load_audio(str(audio_path))
        
        result = self.whisperx.align(
            result["segments"],
            self.align_model,
            self.align_metadata,
            audio,
            self.device,
            return_char_alignments=False
        )
        
        print("✅ 时间戳对齐完成")
        return result
    
    def diarize_speakers(self, audio_path: Path, min_speakers: int = 2, max_speakers: int = 2) -> Dict:
        """
        说话人分离
        
        Args:
            audio_path: 音频文件路径
            min_speakers: 最少说话人数
            max_speakers: 最多说话人数
            
        Returns:
            说话人分离结果
        """
        self.load_diarize_model()
        
        print(f"👥 正在进行说话人分离（{min_speakers}-{max_speakers}人）...")
        audio = self.whisperx.load_audio(str(audio_path))
        
        diarize_segments = self.diarize_model(
            audio,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        print("✅ 说话人分离完成")
        return diarize_segments
    
    def assign_speakers(self, result: Dict, diarize_segments: Dict) -> Dict:
        """
        将说话人标记分配到转写结果
        
        Args:
            result: 对齐后的转写结果
            diarize_segments: 说话人分离结果
            
        Returns:
            带说话人标记的结果
        """
        print("🔗 正在分配说话人标记...")
        result = self.whisperx.assign_word_speakers(diarize_segments, result)
        print("✅ 说话人标记分配完成")
        return result
    
    def format_result(self, result: Dict) -> List[Dict]:
        """
        格式化结果为统一格式
        
        Args:
            result: WhisperX 结果
            
        Returns:
            格式化的对话列表 [{'speaker': 'Speaker 1', 'text': '...'}]
        """
        dialogues = []
        
        for segment in result.get("segments", []):
            speaker = segment.get("speaker", "SPEAKER_00")
            text = segment.get("text", "").strip()
            
            if text:
                # 转换说话人标记格式
                # SPEAKER_00 -> Speaker 1
                speaker_num = int(speaker.split("_")[-1]) + 1
                speaker_label = f"Speaker {speaker_num}"
                
                dialogues.append({
                    'speaker': speaker_label,
                    'text': text
                })
        
        return dialogues
    
    def transcribe(self, 
                   audio_path: Path,
                   enable_diarization: bool = True,
                   min_speakers: int = 2,
                   max_speakers: int = 2) -> Optional[List[Dict]]:
        """
        完整的转写流程（一站式方法）
        
        Args:
            audio_path: 音频文件路径
            enable_diarization: 是否启用说话人分离
            min_speakers: 最少说话人数
            max_speakers: 最多说话人数
            
        Returns:
            对话列表
        """
        print("\n" + "="*60)
        print("🎙️  WhisperX 语音转写")
        print("="*60 + "\n")
        
        try:
            # 1. 转写音频
            result = self.transcribe_audio(audio_path)
            if not result:
                return None
            
            # 2. 时间对齐
            result = self.align_timestamps(audio_path, result)
            
            # 3. 说话人分离（可选）
            if enable_diarization:
                if not self.hf_token:
                    print("⚠️  未提供 HF_TOKEN，跳过说话人分离")
                    print("   所有文本将标记为 'Speaker 1'")
                else:
                    diarize_segments = self.diarize_speakers(
                        audio_path,
                        min_speakers,
                        max_speakers
                    )
                    result = self.assign_speakers(result, diarize_segments)
            
            # 4. 格式化结果
            dialogues = self.format_result(result)
            
            print(f"\n✅ 全部完成！共生成 {len(dialogues)} 段对话")
            return dialogues
            
        except Exception as e:
            print(f"\n❌ 转写失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def test_whisperx():
    """测试 WhisperX 功能"""
    print("\n" + "="*60)
    print("🧪 WhisperX 功能测试")
    print("="*60 + "\n")
    
    # 检查依赖
    try:
        import whisperx
        print("✅ WhisperX 已安装")
    except ImportError:
        print("❌ WhisperX 未安装")
        print("\n安装命令:")
        print("  pip3 install git+https://github.com/m-bain/whisperX.git")
        return
    
    try:
        import torch
        print(f"✅ PyTorch 已安装 (版本: {torch.__version__})")
    except ImportError:
        print("❌ PyTorch 未安装")
        print("\n安装命令:")
        print("  pip3 install torch")
        return
    
    # 检查 HF Token
    hf_token = os.getenv('HF_TOKEN')
    if hf_token:
        print(f"✅ HF_TOKEN 已设置: {hf_token[:10]}...")
    else:
        print("⚠️  HF_TOKEN 未设置（说话人分离需要）")
        print("   获取地址: https://huggingface.co/settings/tokens")
    
    print("\n" + "="*60)
    print("✅ 基础检查完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_whisperx()

