"""
主程序入口
提供命令行界面进行访谈转写和清洗
"""

import argparse
import sys
from pathlib import Path
from transcription_processor import TranscriptionProcessor
from config import Config


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='访谈录音转文本工具（支持讯飞/WhisperX）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用讯飞后端（付费，快速，支持说话人分离）
  python main.py -f interview.mp3 --backend iflytek
  
  # 使用WhisperX后端（免费，较慢，支持说话人分离）
  python main.py -f interview.mp3 --backend whisperx
  
  # 批量处理目录下所有音频
  python main.py -d ./audio_files/
  
  # 自定义说话人标签
  python main.py -f interview.mp3 --speaker1 "访谈者" --speaker2 "受访者"
  
  # 指定输出文件名
  python main.py -f interview.mp3 -o "访谈记录"
        """
    )
    
    # 互斥参数组：文件或目录
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-f', '--file',
        type=str,
        help='单个音频文件路径'
    )
    input_group.add_argument(
        '-d', '--dir',
        type=str,
        help='音频文件目录（批量处理）'
    )
    
    # 说话人标签
    parser.add_argument(
        '--speaker1',
        type=str,
        default='访谈者',
        help='说话人1的标签（默认：访谈者）'
    )
    parser.add_argument(
        '--speaker2',
        type=str,
        default='受访者',
        help='说话人2的标签（默认：受访者）'
    )
    
    # 输出选项
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='输出文件名（不含扩展名，仅单文件模式）'
    )
    
    # 后端选择
    parser.add_argument(
        '--backend',
        type=str,
        choices=['iflytek', 'whisperx'],
        default=None,
        help='选择转写后端：iflytek（讯飞）或 whisperx（默认使用config.py配置）'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 确定使用的后端
    backend = args.backend or Config.DEFAULT_BACKEND
    
    # 验证配置
    try:
        Config.validate(backend)
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        if backend == 'iflytek':
            print("\n请在 config.py 中设置讯飞API密钥：")
            print("  - IFLYTEK_APPID")
            print("  - IFLYTEK_SECRET_KEY")
            print("\n获取密钥: https://www.xfyun.cn/")
        elif backend == 'whisperx':
            print("\nWhisperX 配置说明：")
            print("  1. 安装依赖: pip3 install git+https://github.com/m-bain/whisperX.git")
            print("  2. 获取HF Token: https://huggingface.co/settings/tokens")
            print("  3. 设置到 config.py 的 HF_TOKEN")
        sys.exit(1)
    
    # 构建说话人标签映射
    speaker_labels = {
        'Speaker 1': args.speaker1,
        'Speaker 2': args.speaker2
    }
    
    # 创建处理器
    processor = TranscriptionProcessor(backend=backend)
    
    print("\n" + "="*60)
    print("🎙️  访谈录音转文本工具")
    print(f"   后端: {backend.upper()}")
    print("="*60)
    
    # 处理文件或目录
    try:
        if args.file:
            # 单文件处理
            success = processor.process_single_file(
                args.file,
                speaker_labels=speaker_labels,
                output_name=args.output
            )
            sys.exit(0 if success else 1)
        
        elif args.dir:
            # 批量处理
            if args.output:
                print("⚠️  批量模式下忽略 -o/--output 参数")
            processor.process_batch(
                args.dir,
                speaker_labels=speaker_labels
            )
            sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

