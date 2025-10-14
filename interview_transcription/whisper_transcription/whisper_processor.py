# -*- coding: utf-8 -*-
"""
Whisper 音视频转文本处理器
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime
import whisper
from typing import Optional, List, Dict
import config


class WhisperProcessor:
    """Whisper 转录处理类"""
    
    def __init__(self, model_name: str = None):
        """
        初始化 Whisper 处理器
        
        Args:
            model_name: 模型名称，如不指定则使用配置文件中的设置
        """
        self.model_name = model_name or config.WHISPER_MODEL
        self.device = config.DEVICE
        self.model = None
        self.load_model()
        
    def load_model(self):
        """加载 Whisper 模型"""
        print(f"正在加载 Whisper 模型: {self.model_name}")
        print(f"使用设备: {self.device}")
        
        start_time = time.time()
        self.model = whisper.load_model(self.model_name, device=self.device)
        load_time = time.time() - start_time
        
        print(f"模型加载完成，耗时: {load_time:.2f} 秒")
        
    def transcribe_file(self, 
                       audio_path: str, 
                       output_dir: str = None,
                       output_formats: List[str] = None) -> Dict:
        """
        转录单个音视频文件
        
        Args:
            audio_path: 音视频文件路径
            output_dir: 输出目录，如不指定则使用配置文件中的设置
            output_formats: 输出格式列表，如不指定则使用配置文件中的设置
            
        Returns:
            转录结果字典
        """
        # 检查文件是否存在
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"文件不存在: {audio_path}")
        
        # 检查文件格式
        file_ext = Path(audio_path).suffix.lower()
        if file_ext not in config.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # 设置输出目录和格式
        output_dir = output_dir or config.OUTPUT_DIR
        output_formats = output_formats or config.OUTPUT_FORMATS
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取文件名（不含扩展名）
        file_name = Path(audio_path).stem
        
        print(f"\n{'='*60}")
        print(f"开始转录: {Path(audio_path).name}")
        print(f"{'='*60}")
        
        # 开始转录
        start_time = time.time()
        
        result = self.model.transcribe(
            audio_path,
            language=config.LANGUAGE,
            task=config.TASK,
            verbose=config.VERBOSE,
            fp16=config.FP16,
            temperature=config.TEMPERATURE,
            initial_prompt=config.INITIAL_PROMPT
        )
        
        transcribe_time = time.time() - start_time
        
        print(f"\n转录完成，耗时: {transcribe_time:.2f} 秒")
        
        # 保存结果
        self._save_results(result, file_name, output_dir, output_formats)
        
        # 添加元数据
        result['metadata'] = {
            'file_name': Path(audio_path).name,
            'model': self.model_name,
            'language': config.LANGUAGE or result.get('language', 'unknown'),
            'duration': result.get('segments', [{}])[-1].get('end', 0) if result.get('segments') else 0,
            'transcribe_time': transcribe_time,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
    
    def _save_results(self, 
                     result: Dict, 
                     file_name: str, 
                     output_dir: str, 
                     output_formats: List[str]):
        """
        保存转录结果到多种格式
        
        Args:
            result: 转录结果
            file_name: 文件名
            output_dir: 输出目录
            output_formats: 输出格式列表
        """
        print(f"\n保存结果到: {output_dir}")
        
        for fmt in output_formats:
            output_path = os.path.join(output_dir, f"{file_name}.{fmt}")
            
            if fmt == "txt":
                self._save_txt(result, output_path)
            elif fmt == "json":
                self._save_json(result, output_path)
            elif fmt == "srt":
                self._save_srt(result, output_path)
            elif fmt == "vtt":
                self._save_vtt(result, output_path)
            elif fmt == "tsv":
                self._save_tsv(result, output_path)
            else:
                print(f"警告: 不支持的输出格式 {fmt}")
                continue
            
            print(f"  ✓ 已保存: {output_path}")
    
    def _save_txt(self, result: Dict, output_path: str):
        """保存为纯文本格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            if config.INCLUDE_TIMESTAMPS and 'segments' in result:
                for segment in result['segments']:
                    start = self._format_timestamp(segment['start'])
                    end = self._format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    f.write(f"[{start} --> {end}] {text}\n")
            else:
                f.write(result['text'])
    
    def _save_json(self, result: Dict, output_path: str):
        """保存为 JSON 格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def _save_srt(self, result: Dict, output_path: str):
        """保存为 SRT 字幕格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            if 'segments' in result:
                for i, segment in enumerate(result['segments'], start=1):
                    start = self._format_timestamp_srt(segment['start'])
                    end = self._format_timestamp_srt(segment['end'])
                    text = segment['text'].strip()
                    
                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
    
    def _save_vtt(self, result: Dict, output_path: str):
        """保存为 VTT 字幕格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            if 'segments' in result:
                for segment in result['segments']:
                    start = self._format_timestamp_vtt(segment['start'])
                    end = self._format_timestamp_vtt(segment['end'])
                    text = segment['text'].strip()
                    
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
    
    def _save_tsv(self, result: Dict, output_path: str):
        """保存为 TSV 格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("start\tend\ttext\n")
            
            if 'segments' in result:
                for segment in result['segments']:
                    start = segment['start']
                    end = segment['end']
                    text = segment['text'].strip().replace('\t', ' ')
                    f.write(f"{start:.2f}\t{end:.2f}\t{text}\n")
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """格式化时间戳 (MM:SS)"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def _format_timestamp_srt(seconds: float) -> str:
        """格式化 SRT 时间戳 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_timestamp_vtt(seconds: float) -> str:
        """格式化 VTT 时间戳 (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def main():
    """主函数 - 用于单文件测试"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python whisper_processor.py <音视频文件路径>")
        print("示例: python whisper_processor.py input/test.mp3")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    # 创建处理器
    processor = WhisperProcessor()
    
    # 转录文件
    result = processor.transcribe_file(audio_path)
    
    # 打印摘要
    print(f"\n{'='*60}")
    print("转录摘要:")
    print(f"{'='*60}")
    print(f"文件: {result['metadata']['file_name']}")
    print(f"语言: {result['metadata']['language']}")
    print(f"时长: {result['metadata']['duration']:.2f} 秒")
    print(f"转录耗时: {result['metadata']['transcribe_time']:.2f} 秒")
    print(f"\n文本预览:")
    print(result['text'][:200] + "..." if len(result['text']) > 200 else result['text'])


if __name__ == "__main__":
    main()

