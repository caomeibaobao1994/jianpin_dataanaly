# WhisperX 安装和配置指南

本指南详细说明如何在您的电脑上安装和配置 WhisperX，实现免费的语音转写和说话人分离。

## 📋 您的电脑配置

✅ **MacBook Pro (2018/2019)**  
✅ **Intel Core i5-8279U @ 2.4GHz (4核8线程)**  
✅ **8GB 内存**  
✅ **macOS 系统**  
✅ **Python 3.9.12**

**结论**：您的配置完全满足 WhisperX 运行要求！

## 🎯 预期性能

使用 **small** 模型（推荐）：
- 10分钟音频 → 约 10-15 分钟处理
- 30分钟音频 → 约 30-45 分钟处理
- 60分钟音频 → 约 60-90 分钟处理

## 📦 安装步骤

### 第一步：安装 ffmpeg

ffmpeg 是音频处理必需工具。

```bash
# 检查是否已安装
ffmpeg -version

# 如果未安装，使用 Homebrew 安装
brew install ffmpeg

# 验证安装
ffmpeg -version
```

### 第二步：安装 WhisperX

```bash
# 进入项目目录
cd /Users/sunwenbo/Documents/RUC/github/jianpin_dataanaly/interview_transcription

# 安装 WhisperX（会自动安装所有依赖）
pip3 install git+https://github.com/m-bain/whisperX.git

# 可能需要等待 3-5 分钟
```

**期望输出：**
```
Successfully installed whisperx-...
Successfully installed torch-...
Successfully installed faster-whisper-...
...
```

### 第三步：验证安装

```bash
# 运行测试脚本
python3 whisperx_api.py
```

**期望输出：**
```
✅ WhisperX 已安装
✅ PyTorch 已安装 (版本: 2.x.x)
⚠️  HF_TOKEN 未设置（说话人分离需要）
```

## 🔑 配置 Hugging Face Token（说话人分离必需）

### 为什么需要？

WhisperX 的说话人分离功能使用 pyannote.audio 模型，该模型托管在 Hugging Face 上，需要账号验证。

### 获取步骤

#### 1. 注册 Hugging Face 账号

访问：https://huggingface.co/join  
填写信息注册（完全免费）

#### 2. 接受模型使用协议

访问：https://huggingface.co/pyannote/speaker-diarization  
点击：**"Agree and access repository"**

访问：https://huggingface.co/pyannote/segmentation  
点击：**"Agree and access repository"**

#### 3. 生成 Access Token

1. 访问：https://huggingface.co/settings/tokens
2. 点击：**"New token"**
3. 名称填写：`whisperx_token`
4. 类型选择：**Read**
5. 点击：**"Generate token"**
6. **复制** 生成的 Token（类似：`hf_xxxxxxxxxxxxx`）

#### 4. 配置到项目

编辑 `config.py` 文件：

```python
# 找到这一行（约第40行）
HF_TOKEN = os.getenv('HF_TOKEN', '')

# 修改为（填入你的Token）
HF_TOKEN = os.getenv('HF_TOKEN', 'hf_xxxxxxxxxxxxx你的Token')
```

或者设置环境变量（推荐）：

```bash
# 在 ~/.zshrc 或 ~/.bash_profile 中添加
export HF_TOKEN='hf_xxxxxxxxxxxxx你的Token'

# 重新加载配置
source ~/.zshrc
```

## ✅ 完整验证

运行完整测试：

```bash
# 1. 测试基础功能
python3 whisperx_api.py
```

**期望输出：**
```
✅ WhisperX 已安装
✅ PyTorch 已安装 (版本: 2.x.x)
✅ HF_TOKEN 已设置: hf_xxxxxxxx...
✅ 基础检查完成
```

```bash
# 2. 测试配置验证
python3 -c "from config import Config; Config.validate('whisperx')"
```

**期望输出：**
```
# 没有错误输出，或者：
⚠️  警告: 未设置 HF_TOKEN，将无法使用说话人分离功能
```

## 🚀 开始使用

### 测试转写（无说话人分离）

```bash
# 准备一个测试音频（1-2分钟）
python3 main.py -f test.mp3 --backend whisperx
```

**处理过程：**
```
🔧 使用后端: WhisperX (模型: small)
📥 正在加载 Whisper 模型: small
   首次使用会自动下载模型，请耐心等待...
✅ Whisper 模型加载完成
📄 正在加载音频: test.mp3
🎤 正在进行语音转写...
✅ 转写完成
```

### 测试说话人分离

```bash
# 确保已配置 HF_TOKEN
python3 main.py -f interview.mp3 --backend whisperx --speaker1 "访谈者" --speaker2 "受访者"
```

**首次使用会下载说话人分离模型：**
```
📥 正在加载说话人分离模型...
   首次使用会自动下载模型，请耐心等待...
Downloading: pyannote/speaker-diarization...
✅ 说话人分离模型加载完成
👥 正在进行说话人分离（2-2人）...
✅ 说话人分离完成
```

## 📊 模型大小选择

编辑 `config.py`：

```python
WHISPERX_MODEL = 'small'  # 修改这里
```

| 模型 | 大小 | 准确率 | 速度 | 推荐 |
|------|------|--------|------|------|
| tiny | 75MB | 较低 | 最快 | 测试用 |
| base | 142MB | 一般 | 快 | 要求不高 |
| **small** | 466MB | **良好** | **中等** | **推荐** ⭐ |
| medium | 1.5GB | 很好 | 较慢 | 高要求 |
| large | 2.9GB | 最好 | 慢 | 不推荐（您的电脑内存不足）|

**建议**：使用 **small** 模型，准确率和速度的最佳平衡。

## 🔧 常见问题

### Q1: 安装 WhisperX 失败

**错误信息：** `error: command 'clang' failed`

**解决方法：**
```bash
# 安装 Xcode Command Line Tools
xcode-select --install
```

### Q2: 提示缺少 torch

```bash
pip3 install torch
```

### Q3: 下载模型很慢

**原因**：模型托管在国外服务器

**解决方法：**
- 使用科学上网
- 或者耐心等待（首次下载，后续会缓存）

### Q4: 运行时内存不足

**解决方法：**
- 使用更小的模型（tiny 或 base）
- 关闭其他应用释放内存
- 处理较短的音频

### Q5: 说话人分离失败

**错误信息：** `401 Client Error: Unauthorized`

**原因**：HF_TOKEN 未设置或无效

**解决方法：**
1. 确认已在 Hugging Face 接受模型协议
2. 检查 Token 是否正确复制到 config.py
3. 重新生成 Token

### Q6: 处理速度太慢

**正常现象**：CPU 模式下，处理速度约为音频时长的 1 倍

**优化方法：**
- 使用更小的模型（base）
- 让电脑挂机处理
- 批量处理时可以过夜运行

## 💡 使用技巧

### 1. 测试流程

```bash
# 步骤1: 用1分钟音频快速测试
python3 main.py -f test_1min.mp3 --backend whisperx

# 步骤2: 确认效果后处理完整音频
python3 main.py -f full_interview.mp3 --backend whisperx
```

### 2. 批量处理

```bash
# 晚上开始批量处理，让电脑过夜运行
python3 main.py -d ./audio_files/ --backend whisperx
```

### 3. 混合使用

```bash
# 小数据用 WhisperX（免费）
python3 main.py -f interview1.mp3 --backend whisperx

# 大数据用讯飞（快速）
python3 main.py -d ./many_files/ --backend iflytek
```

## 📝 配置检查清单

安装完成后，请确认：

- [ ] ffmpeg 已安装（`ffmpeg -version`）
- [ ] WhisperX 已安装（`python3 whisperx_api.py`）
- [ ] Hugging Face 账号已注册
- [ ] 模型协议已接受（speaker-diarization + segmentation）
- [ ] HF_TOKEN 已配置到 config.py
- [ ] 配置验证通过（`Config.validate('whisperx')`）
- [ ] 测试音频转写成功

## 🎉 完成

恭喜！您已成功配置 WhisperX，现在可以：

```bash
# 免费处理访谈录音
python3 main.py -f interview.mp3 --backend whisperx

# 享受完整的文本清洗功能
# 输出文件会自动保存到 output/ 目录
```

---

**有问题？** 随时询问！

