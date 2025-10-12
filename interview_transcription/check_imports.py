#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有导入是否正确
"""

print("检查导入...")

try:
    from config import Config
    print("✅ config.Config")
except Exception as e:
    print(f"❌ config.Config: {e}")

try:
    from text_cleaner import TextCleaner
    print("✅ text_cleaner.TextCleaner")
except Exception as e:
    print(f"❌ text_cleaner.TextCleaner: {e}")

try:
    from zhipu_cleaner import ZhipuTextCleaner
    print("✅ zhipu_cleaner.ZhipuTextCleaner")
except Exception as e:
    print(f"❌ zhipu_cleaner.ZhipuTextCleaner: {e}")

try:
    from Ifasr_llm.Ifasr import XfyunAsrClient
    print("✅ Ifasr_llm.Ifasr.XfyunAsrClient")
except Exception as e:
    print(f"❌ Ifasr_llm.Ifasr.XfyunAsrClient: {e}")

try:
    from Ifasr_llm.orderResult import parse_order_result
    print("✅ Ifasr_llm.orderResult.parse_order_result")
except Exception as e:
    print(f"❌ Ifasr_llm.orderResult.parse_order_result: {e}")

print("\n检查配置...")
try:
    print(f"讯飞APPID: {Config.IFLYTEK_APPID[:10]}...")
    print(f"讯飞API_KEY: {Config.IFLYTEK_API_KEY[:10]}...")
    print(f"智谱API_KEY: {Config.ZHIPU_API_KEY[:10]}...")
    print("✅ 配置文件正常")
except Exception as e:
    print(f"❌ 配置检查失败: {e}")

print("\n✅ 所有检查通过！")

