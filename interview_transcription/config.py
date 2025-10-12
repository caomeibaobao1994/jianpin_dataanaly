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
    
    # ============ 讯飞API配置 ============
    # 请在.env文件中设置，或直接在这里填写
    IFLYTEK_APPID = os.getenv('IFLYTEK_APPID', 'c0d9df4d')
    IFLYTEK_SECRET_KEY = os.getenv('IFLYTEK_SECRET_KEY', '206af4dddefea1c442f33f39c11ad96f')
    
    # 大模型API（新版，推荐）
    IFLYTEK_API_KEY = os.getenv('IFLYTEK_API_KEY', '206af4dddefea1c442f33f39c11ad96f')
    IFLYTEK_API_SECRET = os.getenv('IFLYTEK_API_SECRET', 'ZDdkNDE2NTQxNDhhYzI1ZGMwOTA0ZGJh')
    
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
    
    # ============ 智谱AI配置 ============
    # 用于AI辅助文本优化和减贫措施分析
    ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', 'dfabbf5e418647a1b6618619ec26ce64.qfhvaSesDwlL1EYm')
    ZHIPU_MODEL = os.getenv('ZHIPU_MODEL', 'glm-4-flash')  # 可选: glm-4, glm-4-flash
    ZHIPU_BASE_URL = 'https://open.bigmodel.cn/api/paas/v4'
    
    # ============ 任务轮询参数 ============
    POLL_INTERVAL = 5  # 秒
    MAX_POLL_TIME = 3600  # 最长等待1小时
    
    @classmethod
    def validate(cls):
        """验证必要配置是否完整"""
        errors = []
        
        if not cls.IFLYTEK_APPID:
            errors.append("缺少 IFLYTEK_APPID")
        if not cls.IFLYTEK_API_KEY:
            errors.append("缺少 IFLYTEK_API_KEY")
        if not cls.IFLYTEK_API_SECRET:
            errors.append("缺少 IFLYTEK_API_SECRET")
        
        if errors:
            raise ValueError(f"配置错误: {', '.join(errors)}")
        
        return True

