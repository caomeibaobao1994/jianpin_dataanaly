# 访谈录音转文本工具

基于多种后端（讯飞/WhisperX）的访谈录音自动转写和深度文本清洗工具，专为两人对话访谈场景设计。

## ✨ 功能特性

- 🎤 **多后端支持**：讯飞语音转写（付费，快）或 WhisperX（免费，本地）
- 👥 **说话人分离**：自动识别两人对话
- 🧹 **深度清洗**：去除语气词、口语转书面语、去重复、标点规范化
- 📦 **灵活切换**：可随时切换不同后端

## 🎯 后端对比

| 特性 | 讯飞 | WhisperX |
|------|------|----------|
| **成本** | 付费（¥0.3-0.5/分钟）| 免费 |
| **速度** | 快（约0.3倍音频时长）| 较慢（约1倍音频时长）|
| **准确率** | 90-95% | 85-90% |
| **说话人分离** | ✅ 自动 | ✅ 自动 |
| **配置难度** | 简单 | 中等 |
| **隐私** | 上传服务器 | 本地处理 |

## 🚀 快速开始

### 1. 安装基础依赖

```bash
cd interview_transcription
pip3 install requests
```

### 2. 选择后端并配置

#### 方案A：使用讯飞（推荐用于大量数据）

1. 注册讯飞账号：https://www.xfyun.cn/
2. 创建应用，开通"语音转写"服务
3. 充值（约¥50起）
4. 编辑 `config.py`：
   ```python
   IFLYTEK_APPID = '你的APPID'
   IFLYTEK_SECRET_KEY = '你的SecretKey'
   ```

#### 方案B：使用WhisperX（推荐用于少量数据）

1. 安装WhisperX：
   ```bash
   # 安装ffmpeg（如果没有）
   brew install ffmpeg
   
   # 安装WhisperX
   pip3 install git+https://github.com/m-bain/whisperX.git
   ```

2. 获取Hugging Face Token（说话人分离需要）：
   - 访问：https://huggingface.co/
   - 注册账号
   - 访问：https://huggingface.co/pyannote/speaker-diarization
   - 点击 "Agree and access repository"
   - 获取Token：https://huggingface.co/settings/tokens

3. 编辑 `config.py`：
   ```python
   HF_TOKEN = '你的HuggingFace Token'
   DEFAULT_BACKEND = 'whisperx'  # 设为默认后端
   ```

### 3. 开始使用

```bash
# 使用讯飞
python3 main.py -f interview.mp3 --backend iflytek

# 使用WhisperX
python3 main.py -f interview.mp3 --backend whisperx

# 使用默认后端（config.py中配置的）
python3 main.py -f interview.mp3
```

## 📖 使用示例

### 基础用法

```bash
# 处理单个文件
python3 main.py -f interview.mp3

# 批量处理
python3 main.py -d ./audio_files/

# 自定义说话人标签
python3 main.py -f interview.mp3 --speaker1 "研究者" --speaker2 "受访者"

# 指定输出文件名
python3 main.py -f interview.mp3 -o "2024年1月访谈"
```

### 后端切换

```bash
# 临时使用讯飞
python3 main.py -f test.mp3 --backend iflytek

# 临时使用WhisperX
python3 main.py -f test.mp3 --backend whisperx
```

## 📂 输出结果

处理完成后，文件保存在 `output/` 目录：

```
output/
├── interview_raw.txt      # 原始转写文本
└── interview_cleaned.txt  # 深度清洗后的文本
```

**示例输出：**

```
访谈者：您觉得这个项目怎么样？

受访者：我觉得这个项目很好，很有前景。
```

## ⚙️ 自定义配置

编辑 `config.py`：

```python
# 后端选择
DEFAULT_BACKEND = 'iflytek'  # 或 'whisperx'

# WhisperX模型大小（如使用WhisperX）
WHISPERX_MODEL = 'small'  # tiny/base/small/medium/large

# 自定义语气词
FILLER_WORDS = ['嗯', '啊', '呃', '那个', ...]

# 自定义口语映射
COLLOQUIAL_TO_FORMAL = {
    '咋': '怎么',
    '啥': '什么',
    ...
}
```

## 🔧 完整安装指南

详见 `WHISPERX_SETUP.md`（WhisperX安装配置指南）

## 📊 使用建议

### 访谈数量 < 5个
**推荐：WhisperX**
- ✅ 完全免费
- ✅ 隐私保护（本地处理）
- ⚠️ 需要20分钟配置
- ⚠️ 处理较慢（可挂机）

### 访谈数量 > 10个
**推荐：讯飞**
- ✅ 速度快
- ✅ 准确率略高
- ⚠️ 需要充值

### 折中方案
小批量用WhisperX，大批量用讯飞

## ❓ 常见问题

**Q: 如何切换后端？**  
A: 使用 `--backend` 参数，或修改 `config.py` 的 `DEFAULT_BACKEND`

**Q: WhisperX需要GPU吗？**  
A: 不需要，CPU即可运行（您的电脑配置足够）

**Q: 说话人识别不准确？**  
A: 确保录音质量高、两人声音有明显区分

**Q: 如何只使用文本清洗？**  
A: 运行 `python3 clean_existing_text.py input.txt`

## 📁 项目结构

```
interview_transcription/
├── config.py                    # 配置管理
├── iflytek_api.py              # 讯飞API封装
├── whisperx_api.py             # WhisperX封装
├── text_cleaner.py             # 文本清洗
├── transcription_processor.py  # 主处理流程
├── main.py                     # 命令行入口
├── requirements.txt            # 依赖说明
├── README.md                   # 本文档
└── WHISPERX_SETUP.md          # WhisperX详细配置
```

## 🆘 获取帮助

```bash
python3 main.py -h
```

---

**开发者**: 访谈录音转文本系统  
**支持**: 讯飞语音转写 + OpenAI WhisperX
