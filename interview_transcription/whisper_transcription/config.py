"""
Whisper 转录配置文件
"""
import os

# ==================== 环境配置 ====================
# Python 环境路径
PYTHON_ENV = "/opt/anaconda3/envs/jianpin/bin/python"

# ==================== Whisper 模型配置 ====================
# 模型选择: tiny, base, small, medium, large, large-v2, large-v3
# tiny: 最快，精度较低 (~1GB)
# base: 较快，精度一般 (~1GB)
# small: 平衡选择 (~2GB)
# medium: 精度较高 (~5GB)
# large: 最高精度 (~10GB)
WHISPER_MODEL = "medium"  # 推荐使用 medium 或 small

# 语言设置
LANGUAGE = "zh"  # 中文，可设置为 None 自动检测

# 任务类型: transcribe (转录), translate (翻译成英文)
TASK = "transcribe"

# ==================== 文件路径配置 ====================
# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 输入输出目录
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ==================== 输出格式配置 ====================
# 输出格式列表: txt, json, srt, vtt, tsv
OUTPUT_FORMATS = ["txt", "json", "srt"]

# 是否在文本中包含时间戳
INCLUDE_TIMESTAMPS = True

# ==================== 音频处理配置 ====================
# 支持的音视频格式
SUPPORTED_FORMATS = [
    ".mp3", ".mp4", ".wav", ".m4a", ".flac", 
    ".aac", ".ogg", ".wma", ".avi", ".mov", 
    ".mkv", ".webm"
]

# 音频采样率（Whisper 默认使用 16000Hz）
SAMPLE_RATE = 16000

# ==================== 性能配置 ====================
# 设备选择: "cuda" (GPU), "cpu"
# 自动检测 GPU
import torch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 批处理大小
BATCH_SIZE = 16

# FP16 精度（GPU 上可用，速度更快）
FP16 = True if DEVICE == "cuda" else False

# ==================== 其他配置 ====================
# 详细日志
VERBOSE = True

# 保留原始音频文件
KEEP_AUDIO = True

# 温度参数（控制生成的随机性，0-1）
TEMPERATURE = 0.0

# 初始提示词（可以提高特定领域的准确度）
INITIAL_PROMPT = "以下是一段关于扶贫、乡村振兴、农村发展的访谈内容。"

