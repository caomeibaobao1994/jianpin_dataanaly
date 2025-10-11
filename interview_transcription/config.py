"""
配置管理模块
管理讯飞API密钥和系统参数
"""

import os
from pathlib import Path

# 尝试加载 dotenv（可选依赖）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，跳过
    pass


class Config:
    """系统配置类"""
    
    # ============ 后端选择 ============
    # 可选: 'iflytek' (讯飞) 或 'whisperx' (WhisperX)
    DEFAULT_BACKEND = os.getenv('TRANSCRIPTION_BACKEND', 'iflytek')
    
    # ============ 讯飞API配置 ============
    # 请在.env文件中设置，或直接在这里填写
    IFLYTEK_APPID = os.getenv('IFLYTEK_APPID', 'c0d9df4d')
    IFLYTEK_SECRET_KEY = os.getenv('IFLYTEK_SECRET_KEY', '4c4079c19d674ee01c14f3faadec89e4')
    
    # ============ WhisperX配置 ============
    # 模型大小: tiny/base/small/medium/large
    # small: 推荐，准确率高，速度适中（~466MB）
    WHISPERX_MODEL = os.getenv('WHISPERX_MODEL', 'small')
    # 设备: cpu 或 cuda（如有GPU）
    WHISPERX_DEVICE = os.getenv('WHISPERX_DEVICE', 'cpu')
    # 计算精度: int8/float16/float32
    WHISPERX_COMPUTE_TYPE = os.getenv('WHISPERX_COMPUTE_TYPE', 'int8')
    # Hugging Face Token（说话人分离必需）
    # 获取地址: https://huggingface.co/settings/tokens
    HF_TOKEN = os.getenv('HF_TOKEN', '')
    
    # ============ 音频参数 ============
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.flac']
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    
    # ============ 转写参数 ============
    # 是否开启说话人分离（两人对话必须开启）
    ENABLE_SPEAKER_SEPARATION = True
    # 说话人数量
    SPEAKER_NUMBER = 2
    # 语言（中文）
    LANGUAGE = 'zh_cn'
    # 是否加标点
    HAS_PARTICIPLE = True
    
    # ============ 清洗参数 ============
    # 语气词列表（深度清洗）
    FILLER_WORDS = [
        '嗯', '啊', '呃', '额', '哦', '诶', '唉',
        '那个', '这个', '就是', '然后', '嘛', '吧',
        '呢', '哈', '嘿', '哟', '喂', '嗨',
        '嗯嗯', '啊啊', '呃呃', '哦哦',
    ]
    
    # 口语化表达 → 书面语映射
    COLLOQUIAL_TO_FORMAL = {
        '咋': '怎么',
        '咋样': '怎么样',
        '啥': '什么',
        '咋办': '怎么办',
        '整': '做',
        '弄': '处理',
        '搞': '进行',
        '挺': '很',
        '特': '特别',
        '超': '非常',
        '蛮': '比较',
        '挺好的': '很好',
        '可牛了': '非常厉害',
        '杠杠的': '非常好',
    }
    
    # 重复词检测阈值
    REPEAT_THRESHOLD = 3
    
    # ============ 任务轮询参数 ============
    POLL_INTERVAL = 5  # 秒
    MAX_POLL_TIME = 3600  # 最长等待1小时
    
    # ============ 输出参数 ============
    OUTPUT_DIR = Path('output')
    SAVE_RAW_TEXT = True  # 是否保存原始文本
    SAVE_CLEANED_TEXT = True  # 是否保存清洗后文本
    SAVE_JSON = False  # 是否保存JSON格式
    
    # ============ 日志参数 ============
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'transcription.log'
    
    @classmethod
    def validate(cls, backend=None):
        """
        验证必要配置是否完整
        
        Args:
            backend: 指定后端 ('iflytek' 或 'whisperx')，None则使用默认
        """
        backend = backend or cls.DEFAULT_BACKEND
        errors = []
        
        if backend == 'iflytek':
            if not cls.IFLYTEK_APPID:
                errors.append("缺少 IFLYTEK_APPID")
            if not cls.IFLYTEK_SECRET_KEY:
                errors.append("缺少 IFLYTEK_SECRET_KEY")
        
        elif backend == 'whisperx':
            # WhisperX 不强制要求 HF_TOKEN，但说话人分离需要
            if not cls.HF_TOKEN:
                print("⚠️  警告: 未设置 HF_TOKEN，将无法使用说话人分离功能")
                print("   获取地址: https://huggingface.co/settings/tokens")
        
        else:
            errors.append(f"未知的后端: {backend}，支持: iflytek, whisperx")
        
        if errors:
            raise ValueError(f"配置错误: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def setup_output_dir(cls):
        """创建输出目录"""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.OUTPUT_DIR

