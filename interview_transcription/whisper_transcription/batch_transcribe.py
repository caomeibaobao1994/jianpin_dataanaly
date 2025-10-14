# -*- coding: utf-8 -*-
"""
批量转录脚本 - 处理文件夹中的所有音视频文件
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse
from whisper_processor import WhisperProcessor
import config


def get_audio_files(input_dir: str) -> list:
    """
    获取目录中所有支持的音视频文件
    
    Args:
        input_dir: 输入目录路径
        
    Returns:
        音视频文件路径列表
    """
    audio_files = []
    
    for file_path in Path(input_dir).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in config.SUPPORTED_FORMATS:
            audio_files.append(str(file_path))
    
    return sorted(audio_files)


def batch_transcribe(input_dir: str = None, 
                     output_dir: str = None,
                     model_name: str = None):
    """
    批量转录音视频文件
    
    Args:
        input_dir: 输入目录，默认使用配置文件中的设置
        output_dir: 输出目录，默认使用配置文件中的设置
        model_name: 模型名称，默认使用配置文件中的设置
    """
    # 使用默认值
    input_dir = input_dir or config.INPUT_DIR
    output_dir = output_dir or config.OUTPUT_DIR
    
    # 检查输入目录
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}")
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有音视频文件
    audio_files = get_audio_files(input_dir)
    
    if not audio_files:
        print(f"警告: 在 {input_dir} 中未找到支持的音视频文件")
        print(f"支持的格式: {', '.join(config.SUPPORTED_FORMATS)}")
        return
    
    print(f"\n{'='*60}")
    print(f"批量转录任务")
    print(f"{'='*60}")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"找到 {len(audio_files)} 个文件")
    print(f"{'='*60}\n")
    
    # 创建处理器（只加载一次模型）
    processor = WhisperProcessor(model_name=model_name)
    
    # 记录统计信息
    success_count = 0
    fail_count = 0
    total_time = 0
    results = []
    
    # 开始处理
    start_time = datetime.now()
    
    for i, audio_path in enumerate(audio_files, start=1):
        print(f"\n处理进度: [{i}/{len(audio_files)}]")
        
        try:
            result = processor.transcribe_file(
                audio_path=audio_path,
                output_dir=output_dir
            )
            
            success_count += 1
            total_time += result['metadata']['transcribe_time']
            results.append({
                'file': Path(audio_path).name,
                'status': 'success',
                'duration': result['metadata']['duration'],
                'transcribe_time': result['metadata']['transcribe_time']
            })
            
        except Exception as e:
            fail_count += 1
            print(f"\n错误: 处理文件失败 - {Path(audio_path).name}")
            print(f"原因: {str(e)}")
            results.append({
                'file': Path(audio_path).name,
                'status': 'failed',
                'error': str(e)
            })
    
    # 打印总结
    end_time = datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*60}")
    print("批量转录完成")
    print(f"{'='*60}")
    print(f"总文件数: {len(audio_files)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"总耗时: {elapsed_time:.2f} 秒")
    print(f"平均每个文件: {elapsed_time/len(audio_files):.2f} 秒")
    print(f"{'='*60}\n")
    
    # 保存处理报告
    save_report(results, output_dir, start_time)


def save_report(results: list, output_dir: str, start_time: datetime):
    """
    保存处理报告
    
    Args:
        results: 处理结果列表
        output_dir: 输出目录
        start_time: 开始时间
    """
    import json
    
    report_path = os.path.join(
        output_dir, 
        f"batch_report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    report = {
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model': config.WHISPER_MODEL,
        'language': config.LANGUAGE,
        'total_files': len(results),
        'success_count': sum(1 for r in results if r['status'] == 'success'),
        'fail_count': sum(1 for r in results if r['status'] == 'failed'),
        'results': results
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"处理报告已保存: {report_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量音视频转文本工具')
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        default=config.INPUT_DIR,
        help=f'输入目录路径 (默认: {config.INPUT_DIR})'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=config.OUTPUT_DIR,
        help=f'输出目录路径 (默认: {config.OUTPUT_DIR})'
    )
    
    parser.add_argument(
        '-m', '--model',
        type=str,
        default=config.WHISPER_MODEL,
        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
        help=f'Whisper 模型 (默认: {config.WHISPER_MODEL})'
    )
    
    args = parser.parse_args()
    
    # 执行批量转录
    batch_transcribe(
        input_dir=args.input,
        output_dir=args.output,
        model_name=args.model
    )


if __name__ == "__main__":
    main()

