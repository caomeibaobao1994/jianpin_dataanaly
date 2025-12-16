# Whisper 音视频转文本工具

基于 OpenAI Whisper 的音视频转文本工具，支持批量处理和多种输出格式。

## 功能特性

- ✅ 支持多种音视频格式（MP3, MP4, WAV, M4A 等）
- ✅ 批量处理功能
- ✅ 多种输出格式（TXT, JSON, SRT, VTT, TSV）
- ✅ 时间戳标记
- ✅ 自动检测或指定语言
- ✅ GPU 加速支持
- ✅ 详细的处理报告

## 环境要求

- Python 3.8+
- FFmpeg（系统级依赖）
- CUDA（可选，用于 GPU 加速）

## 安装步骤

### 1. 安装系统依赖

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
下载 FFmpeg 并添加到系统 PATH

### 2. 安装 Python 依赖

使用指定的 Python 环境：
```bash
/opt/anaconda3/envs/jianpin/bin/pip install -r requirements.txt
```

或在已激活的环境中：
```bash
pip install -r requirements.txt
```

## 使用方法

### 方式一：批量处理（推荐）

1. 将音视频文件放入 `input` 文件夹
2. 运行批量处理脚本：

```bash
# 使用指定环境
/opt/anaconda3/envs/jianpin/bin/python batch_transcribe.py

# 指定输入输出目录
/opt/anaconda3/envs/jianpin/bin/python batch_transcribe.py -i /path/to/input -o /path/to/output

# 指定模型
/opt/anaconda3/envs/jianpin/bin/python batch_transcribe.py -m medium
```

### 方式二：单文件处理

```bash
# 处理单个文件
/opt/anaconda3/envs/jianpin/bin/python whisper_processor.py input/your_audio.mp3
```

### 方式三：Python 脚本调用

```python
from whisper_processor import WhisperProcessor

# 创建处理器
processor = WhisperProcessor(model_name='medium')

# 转录单个文件
result = processor.transcribe_file('input/audio.mp3')

# 访问结果
print(result['text'])  # 转录文本
print(result['segments'])  # 分段信息
print(result['metadata'])  # 元数据
```

## 配置说明

编辑 `config.py` 文件来自定义设置：

### 模型选择
- `tiny`: 最快，精度较低（~39M 参数）
- `base`: 较快，精度一般（~74M 参数）
- `small`: 平衡选择（~244M 参数）⭐ 推荐
- `medium`: 精度较高（~769M 参数）⭐ 推荐
- `large`: 最高精度（~1550M 参数）

### 输出格式
- `txt`: 纯文本（可选时间戳）
- `json`: 完整 JSON 数据
- `srt`: SRT 字幕格式
- `vtt`: WebVTT 字幕格式
- `tsv`: 制表符分隔值

### 其他配置
```python
# 语言设置
LANGUAGE = "zh"  # 中文，设为 None 自动检测

# 输出格式
OUTPUT_FORMATS = ["txt", "json", "srt"]

# 时间戳
INCLUDE_TIMESTAMPS = True

# 初始提示词（提高特定领域准确度）
INITIAL_PROMPT = "以下是一段关于扶贫、乡村振兴、农村发展的访谈内容。"
```

## 支持的文件格式

| 格式 | 扩展名 |
|------|--------|
| 音频 | .mp3, .wav, .m4a, .flac, .aac, .ogg, .wma |
| 视频 | .mp4, .avi, .mov, .mkv, .webm |

## 输出示例

### TXT 格式（带时间戳）
```
[00:00 --> 00:05] 大家好，今天我们来讨论扶贫工作的进展。
[00:05 --> 00:12] 在过去的几年里，我们村取得了显著的成就。
```

### SRT 字幕格式
```
1
00:00:00,000 --> 00:00:05,000
大家好，今天我们来讨论扶贫工作的进展。

2
00:00:05,000 --> 00:00:12,000
在过去的几年里，我们村取得了显著的成就。
```

### JSON 格式
```json
{
  "text": "完整转录文本...",
  "segments": [
    {
      "start": 0.0,
      "end": 5.0,
      "text": "大家好，今天我们来讨论扶贫工作的进展。"
    }
  ],
  "metadata": {
    "file_name": "interview.mp3",
    "model": "medium",
    "language": "zh",
    "duration": 120.5,
    "transcribe_time": 45.2
  }
}
```

## 性能优化

### GPU 加速
如果有 NVIDIA GPU，会自动使用 CUDA 加速：
```python
# config.py 中会自动检测
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
FP16 = True  # GPU 上启用 FP16 加速
```

### 模型下载
首次运行时会自动下载模型，保存在 `~/.cache/whisper/`

### 处理速度参考（medium 模型）
- CPU: 约为实时速度的 0.5-1 倍
- GPU (RTX 3090): 约为实时速度的 5-10 倍

## 目录结构

```
whisper_transcription/
├── config.py                 # 配置文件
├── whisper_processor.py      # 主处理器
├── batch_transcribe.py       # 批量处理脚本
├── requirements.txt          # 依赖列表
├── README.md                 # 使用说明
├── input/                    # 输入目录（放置音视频文件）
└── output/                   # 输出目录（转录结果）
    ├── *.txt                 # 文本文件
    ├── *.json                # JSON 文件
    ├── *.srt                 # 字幕文件
    └── batch_report_*.json   # 批处理报告
```

## 常见问题

### 1. FFmpeg 未安装
**错误:** `ffmpeg: command not found`  
**解决:** 按照安装步骤安装 FFmpeg

### 2. CUDA 不可用
**错误:** `CUDA is not available`  
**解决:** 安装支持 CUDA 的 PyTorch 版本，或使用 CPU 模式

### 3. 内存不足
**错误:** `RuntimeError: CUDA out of memory`  
**解决:** 使用更小的模型（如 small 或 base）

### 4. 模型下载慢
**解决:** 
- 使用代理或 VPN
- 手动下载模型到 `~/.cache/whisper/`

### 5. 转录结果不准确
**解决:** 
- 使用更大的模型（medium 或 large）
- 设置正确的语言参数
- 提供领域相关的初始提示词

## 进阶用法

### 自定义初始提示词
在 `config.py` 中设置：
```python
INITIAL_PROMPT = "这是一段关于农村发展、扶贫政策的访谈。包含政策解读和实践经验。"
```

### 处理特定格式
```bash
# 只处理 MP3 文件
find input/ -name "*.mp3" -exec /opt/anaconda3/envs/jianpin/bin/python whisper_processor.py {} \;
```

### 并行处理
使用 GNU Parallel 加速批量处理：
```bash
find input/ -type f | parallel -j 4 /opt/anaconda3/envs/jianpin/bin/python whisper_processor.py {}
```

## 许可证

本项目使用 Whisper 模型，遵循 MIT 许可证。

## 参考资料

- [OpenAI Whisper 官方仓库](https://github.com/openai/whisper)
- [Whisper 模型介绍](https://openai.com/research/whisper)
- [FFmpeg 官方网站](https://ffmpeg.org/)

## 更新日志

### v1.0.0 (2025-10-13)
- ✨ 初始版本发布
- ✅ 支持批量处理
- ✅ 支持多种输出格式
- ✅ GPU 加速支持



