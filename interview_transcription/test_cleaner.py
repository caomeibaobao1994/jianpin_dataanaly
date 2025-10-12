#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文本清洗功能，特别是说话人段落合并
"""

from text_cleaner import TextCleaner

def test_speaker_merge():
    """测试说话人段落合并功能"""
    
    # 读取转写结果
    with open('output/test_转写结果.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取转写文本部分（跳过头部信息）
    if '转写文本：' in content:
        transcript = content.split('转写文本：')[1].strip()
    else:
        transcript = content
    
    print("="*60)
    print("原始转写文本（有多段连续同一说话人）")
    print("="*60)
    print(transcript)
    
    # 初始化清洗器
    cleaner = TextCleaner()
    
    # 测试1：只合并说话人段落
    print("\n" + "="*60)
    print("处理1：仅合并连续同一说话人段落")
    print("="*60)
    merged_only = cleaner.clean_transcript(
        transcript, 
        merge_speakers=True, 
        deep_clean=False,
        use_ai=False
    )
    print(merged_only)
    
    # 测试2：合并说话人 + 智谱AI智能优化
    print("\n" + "="*60)
    print("处理2：合并说话人 + 智谱AI智能优化")
    print("="*60)
    ai_cleaned = cleaner.clean_transcript(
        transcript, 
        merge_speakers=True, 
        deep_clean=False,  # 不使用规则清洗
        use_ai=True,
        ai_batch_size=3  # 每批处理3个段落
    )
    print(ai_cleaned)
    
    # 保存为两个独立的txt文件
    # 文件1：仅合并说话人
    with open('output/test_仅合并段落.txt', 'w', encoding='utf-8') as f:
        f.write("音频文件：test.MP3\n")
        f.write("处理方式：仅合并连续同一说话人段落\n")
        f.write("="*60 + "\n\n")
        f.write(merged_only)
    
    # 文件2：AI优化
    with open('output/test_AI优化.txt', 'w', encoding='utf-8') as f:
        f.write("音频文件：test.MP3\n")
        f.write("处理方式：合并说话人 + 智谱AI智能优化\n")
        f.write("="*60 + "\n\n")
        if ai_cleaned:
            f.write(ai_cleaned)
        else:
            f.write("AI清洗失败，未能生成结果")
    
    print("\n" + "="*60)
    print("✅ 结果已保存：")
    print("   1. output/test_仅合并段落.txt")
    print("   2. output/test_AI优化.txt")
    print("="*60)
    
    # 统计信息
    original_lines = len([l for l in transcript.split('\n') if l.strip().startswith('【')])
    merged_lines = len([l for l in merged_only.split('\n') if l.strip().startswith('【')])
    
    print(f"\n📊 统计信息：")
    print(f"  原始段落数：{original_lines}")
    print(f"  合并后段落数：{merged_lines}")
    print(f"  减少段落数：{original_lines - merged_lines}")

if __name__ == '__main__':
    test_speaker_merge()

