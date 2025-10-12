#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理访谈音频文件
完整流程：MP3 → 讯飞转写 → 合并段落 → 智谱AI优化 → 减贫措施分析
"""

import os
import json
import time
from pathlib import Path
from typing import List, Optional

# 导入自定义模块
import sys
# 确保能导入Ifasr_llm模块
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from text_cleaner import TextCleaner
from zhipu_cleaner import ZhipuTextCleaner
from poverty_reduction_analyzer import PovertyReductionAnalyzer

# 导入讯飞API模块
from Ifasr_llm.Ifasr import XfyunAsrClient
from Ifasr_llm.orderResult import parse_order_result


class BatchProcessor:
    """批量处理访谈音频文件"""
    
    def __init__(self, 
                 input_dir: str,
                 output_base_dir: str = "output",
                 enable_ai: bool = True,
                 enable_poverty_analysis: bool = True):
        """
        初始化批处理器
        
        Args:
            input_dir: 输入音频文件目录
            output_base_dir: 输出基础目录
            enable_ai: 是否启用智谱AI优化
            enable_poverty_analysis: 是否启用减贫措施分析
        """
        self.input_dir = Path(input_dir)
        self.output_base_dir = Path(output_base_dir)
        self.enable_ai = enable_ai
        self.enable_poverty_analysis = enable_poverty_analysis
        
        # 创建输出目录结构
        self.api_dir = self.output_base_dir / "1_api_responses"
        self.merged_dir = self.output_base_dir / "2_merged_texts"
        self.ai_dir = self.output_base_dir / "3_ai_optimized"
        self.poverty_dir = self.output_base_dir / "4_poverty_reduction_summary"
        
        for dir_path in [self.api_dir, self.merged_dir, self.ai_dir, self.poverty_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化工具
        self.text_cleaner = TextCleaner()
        
        if self.enable_ai:
            try:
                self.ai_cleaner = ZhipuTextCleaner()
                print("✅ 智谱AI优化已初始化")
            except Exception as e:
                print(f"⚠️  智谱AI初始化失败: {e}")
                self.enable_ai = False
        
        if self.enable_poverty_analysis:
            try:
                self.poverty_analyzer = PovertyReductionAnalyzer()
                print("✅ 减贫措施分析器已初始化")
            except Exception as e:
                print(f"⚠️  减贫措施分析器初始化失败: {e}")
                self.enable_poverty_analysis = False
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def get_audio_files(self) -> List[Path]:
        """获取所有音频文件"""
        audio_files = []
        for ext in ['.mp3', '.MP3', '.wav', '.WAV', '.m4a', '.M4A']:
            audio_files.extend(self.input_dir.glob(f"*{ext}"))
        
        # 按文件名排序
        audio_files.sort(key=lambda x: x.name)
        return audio_files
    
    def process_single_file(self, audio_path: Path) -> bool:
        """
        处理单个音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            是否处理成功
        """
        basename = audio_path.stem  # 文件名（不含扩展名）
        print("\n" + "="*70)
        print(f"📄 处理文件: {audio_path.name}")
        print("="*70)
        
        try:
            # 检查是否已处理过
            api_file = self.api_dir / f"{basename}_api.json"
            merged_file = self.merged_dir / f"{basename}_merged.txt"
            ai_file = self.ai_dir / f"{basename}_ai.txt"
            poverty_file = self.poverty_dir / f"{basename}_poverty_summary.txt"
            
            # 如果所有输出文件都存在，跳过
            all_done = api_file.exists() and merged_file.exists()
            if self.enable_ai:
                all_done = all_done and ai_file.exists()
            if self.enable_poverty_analysis:
                all_done = all_done and poverty_file.exists()
            
            if all_done:
                print(f"⏭️  文件已处理，跳过: {audio_path.name}")
                self.stats['skipped'] += 1
                return True
            
            # ========== 步骤1: 讯飞语音转写 ==========
            total_steps = 2 + (1 if self.enable_ai else 0) + (1 if self.enable_poverty_analysis else 0)
            print(f"\n[1/{total_steps}] 🎙️  讯飞语音转写中...")
            
            asr_client = XfyunAsrClient(
                appid=Config.IFLYTEK_APPID,
                access_key_id=Config.IFLYTEK_API_KEY,
                access_key_secret=Config.IFLYTEK_API_SECRET,
                audio_file_path=str(audio_path)
            )
            
            # 获取转写结果
            api_response = asr_client.get_transcribe_result()
            
            # 保存API原始响应
            with open(api_file, 'w', encoding='utf-8') as f:
                json.dump(api_response, f, ensure_ascii=False, indent=2)
            print(f"   ✅ API响应已保存: {api_file.name}")
            
            # 解析转写结果
            transcript_text = parse_order_result(
                api_response, 
                with_speaker=True, 
                debug=False
            )
            
            if not transcript_text:
                raise Exception("转写结果为空")
            
            # ========== 步骤2: 合并段落 ==========
            step_num = 2
            print(f"\n[{step_num}/{total_steps}] 📝 合并连续同一说话人段落...")
            
            merged_text = self.text_cleaner.clean_transcript(
                transcript_text,
                merge_speakers=True,
                deep_clean=False,
                use_ai=False
            )
            
            # 保存合并后的文本
            with open(merged_file, 'w', encoding='utf-8') as f:
                f.write(f"音频文件: {audio_path.name}\n")
                f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write(merged_text)
            print(f"   ✅ 合并文本已保存: {merged_file.name}")
            
            # ========== 步骤3: 智谱AI优化（可选）==========
            ai_text = None
            if self.enable_ai:
                step_num += 1
                print(f"\n[{step_num}/{total_steps}] 🤖 智谱AI智能优化中...")
                
                # 解析为对话列表
                dialogues = self.text_cleaner.parse_speaker_text(merged_text)
                
                # AI优化
                ai_dialogues = self.ai_cleaner.clean_dialogue_batch(
                    dialogues,
                    batch_size=5
                )
                
                # 格式化输出
                ai_text = self.text_cleaner.format_to_text(
                    ai_dialogues,
                    show_speaker=True
                )
                
                # 保存AI优化文本
                with open(ai_file, 'w', encoding='utf-8') as f:
                    f.write(f"音频文件: {audio_path.name}\n")
                    f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n\n")
                    f.write(ai_text)
                print(f"   ✅ AI优化文本已保存: {ai_file.name}")
            
            # ========== 步骤4: 减贫措施分析（可选）==========
            if self.enable_poverty_analysis:
                step_num += 1
                print(f"\n[{step_num}/{total_steps}] 🔍 分析减贫措施中...")
                
                # 使用AI优化后的文本（如果有），否则使用合并后的文本
                analysis_text = ai_text if ai_text else merged_text
                
                # 执行分析
                analysis_result = self.poverty_analyzer.analyze_interview(analysis_text)
                
                # 保存分析结果
                self.poverty_analyzer.save_analysis(
                    analysis_result,
                    str(poverty_file),
                    audio_path.name
                )
            
            print(f"\n✅ 文件处理完成: {audio_path.name}")
            self.stats['success'] += 1
            return True
            
        except Exception as e:
            print(f"\n❌ 处理失败: {audio_path.name}")
            print(f"   错误信息: {str(e)}")
            self.stats['failed'] += 1
            return False
    
    def process_all(self):
        """批量处理所有音频文件"""
        audio_files = self.get_audio_files()
        self.stats['total'] = len(audio_files)
        
        if self.stats['total'] == 0:
            print(f"\n⚠️  未在 {self.input_dir} 中找到音频文件")
            return
        
        print("\n" + "="*70)
        print(f"🎯 批量处理任务")
        print("="*70)
        print(f"输入目录: {self.input_dir}")
        print(f"输出目录: {self.output_base_dir}")
        print(f"音频文件数: {self.stats['total']}")
        print(f"启用AI优化: {'是' if self.enable_ai else '否'}")
        print(f"启用减贫分析: {'是' if self.enable_poverty_analysis else '否'}")
        print("="*70)
        
        # 逐个处理
        for idx, audio_file in enumerate(audio_files, 1):
            print(f"\n进度: {idx}/{self.stats['total']}")
            self.process_single_file(audio_file)
            
            # 避免API请求过快
            if idx < self.stats['total']:
                time.sleep(2)
        
        # 打印最终统计
        self.print_summary()
    
    def print_summary(self):
        """打印处理统计摘要"""
        print("\n" + "="*70)
        print("📊 处理完成统计")
        print("="*70)
        print(f"总文件数: {self.stats['total']}")
        print(f"成功处理: {self.stats['success']} ✅")
        print(f"处理失败: {self.stats['failed']} ❌")
        print(f"已跳过: {self.stats['skipped']} ⏭️")
        print("="*70)
        
        print(f"\n📁 输出文件位置:")
        print(f"   API响应: {self.api_dir}")
        print(f"   合并文本: {self.merged_dir}")
        if self.enable_ai:
            print(f"   AI优化: {self.ai_dir}")
        if self.enable_poverty_analysis:
            print(f"   减贫措施分析: {self.poverty_dir}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='批量处理访谈音频文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 处理mp3data文件夹中的所有音频
  python batch_processor.py -i mp3data
  
  # 处理并启用AI优化
  python batch_processor.py -i mp3data --ai
  
  # 指定输出目录
  python batch_processor.py -i mp3data -o my_output --ai
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='输入音频文件目录'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output',
        help='输出基础目录（默认: output）'
    )
    parser.add_argument(
        '--ai',
        action='store_true',
        help='启用智谱AI智能优化'
    )
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='禁用智谱AI优化（仅转写+合并）'
    )
    parser.add_argument(
        '--poverty-analysis',
        action='store_true',
        default=True,
        help='启用减贫措施分析（默认启用）'
    )
    parser.add_argument(
        '--no-poverty-analysis',
        action='store_true',
        help='禁用减贫措施分析'
    )
    
    args = parser.parse_args()
    
    # 确定是否启用AI
    enable_ai = args.ai or not args.no_ai
    
    # 确定是否启用减贫分析
    enable_poverty_analysis = not args.no_poverty_analysis
    
    # 创建处理器并执行
    processor = BatchProcessor(
        input_dir=args.input,
        output_base_dir=args.output,
        enable_ai=enable_ai,
        enable_poverty_analysis=enable_poverty_analysis
    )
    
    try:
        processor.process_all()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断处理")
        processor.print_summary()
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

