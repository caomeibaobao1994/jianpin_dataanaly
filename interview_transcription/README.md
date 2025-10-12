# 访谈音频批量处理系统

> 完整的访谈音频转写和分析流程：MP3 → 讯飞转写 → 合并段落 → 智谱AI优化 → 减贫措施分析

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 处理流程

```
mp3data/
  ├── interview1.mp3
  ├── interview2.mp3
  └── interview3.mp3
        ↓
   【步骤1：讯飞API语音转写】
   - 自动识别说话人（访谈者/受访者）
   - 添加标点符号
        ↓
   【步骤2：合并连续段落】
   - 合并连续同一说话人的多个段落
   - 提高可读性
        ↓
   【步骤3：智谱AI智能优化】
   - 去除语气词（嗯、啊等）
   - 口语转书面语
   - 优化句子结构
        ↓
   【步骤4：减贫措施智能分析】✨
   - 提取9个维度的减贫措施
   - 总结受访者生活变化
   - 识别工作亮点
        ↓
output/
  ├── 1_api_responses/              # API原始响应JSON
  ├── 2_merged_texts/               # 合并段落后的文本
  ├── 3_ai_optimized/               # AI智能优化文本
  └── 4_poverty_reduction_summary/  # 减贫措施分析报告 ✨
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd interview_transcription
pip install zhipuai requests
```

### 2. 配置API密钥

编辑 `config.py`，填入你的API密钥：

```python
# 讯飞API配置
IFLYTEK_APPID = "你的APPID"
IFLYTEK_API_KEY = "你的API_KEY"
IFLYTEK_API_SECRET = "你的API_SECRET"

# 智谱AI配置
ZHIPU_API_KEY = "你的智谱API_KEY"
```

**API密钥获取地址**：
- 讯飞API：https://www.xfyun.cn/
- 智谱AI：https://open.bigmodel.cn/

### 3. 批量处理音频

```bash
# 完整处理（转写+合并+AI优化+减贫分析）- 推荐！
python batch_processor.py -i mp3data --ai

# 仅转写和合并，不使用AI优化
python batch_processor.py -i mp3data --no-ai

# 不进行减贫措施分析
python batch_processor.py -i mp3data --ai --no-poverty-analysis

# 指定输出目录
python batch_processor.py -i mp3data -o my_output --ai
```

## 📁 项目结构

```
interview_transcription/
├── batch_processor.py              # 批量处理主程序 ⭐
├── config.py                       # 配置管理
├── text_cleaner.py                 # 文本清洗（合并段落）
├── zhipu_cleaner.py                # 智谱AI文本优化
├── poverty_reduction_analyzer.py   # 减贫措施分析器 ✨
├── requirements.txt                # Python依赖包
│
├── Ifasr_llm/                      # 讯飞API封装
│   ├── Ifasr.py                    # 语音转写客户端
│   └── orderResult.py              # 结果解析
│
├── mp3data/                        # 输入音频目录
│   └── *.mp3
│
└── output/                         # 输出目录
    ├── 1_api_responses/            # API原始响应JSON
    ├── 2_merged_texts/             # 合并段落文本
    ├── 3_ai_optimized/             # AI优化文本
    └── 4_poverty_reduction_summary/ # 减贫措施分析报告
```

### 核心模块说明

| 模块 | 功能 | 代码行数 |
|------|------|---------|
| `batch_processor.py` | 批量处理主程序，协调整个流程 | ~350行 |
| `config.py` | 配置管理（API密钥、参数设置） | ~70行 |
| `text_cleaner.py` | 文本清洗和段落合并 | ~390行 |
| `zhipu_cleaner.py` | 智谱AI文本优化 | ~240行 |
| `poverty_reduction_analyzer.py` | 减贫措施智能分析 | ~280行 |

## 📊 输出文件说明

处理完成后，每个音频文件会生成5个输出文件：

```
output/
├── 1_api_responses/
│   └── interview1_api.json         # 讯飞API原始JSON响应
│
├── 2_merged_texts/
│   └── interview1_merged.txt       # 合并段落后的文本
│
├── 3_ai_optimized/
│   └── interview1_ai.txt           # AI智能优化文本
│
└── 4_poverty_reduction_summary/
    ├── interview1_poverty_summary.txt   # 减贫措施分析报告
    └── interview1_poverty_summary.json  # 结构化数据
```

### 输出文件用途

| 文件夹 | 内容 | 用途 |
|--------|------|------|
| `1_api_responses/` | 讯飞API原始JSON响应 | 备份原始数据，可重新解析 |
| `2_merged_texts/` | 合并段落后的文本 | 保留口语化表达，真实还原访谈 |
| `3_ai_optimized/` | AI智能优化文本 | 规范书面表达，适合存档和分析 |
| `4_poverty_reduction_summary/` | 减贫措施分析报告 | 结构化提取9大维度减贫措施 |

## 💡 输出示例对比

### 原始转写（22个段落）
```
【访谈者】比如说造房子呀，
【访谈者】比如说你家小孩读书啊
【受访者】房子造起来了，
【受访者】小孩也大了，
```

### 合并段落（16个段落）
```
【访谈者】比如说造房子呀，比如说你家小孩读书啊

【受访者】房子造起来了，小孩也大了，
```

### AI优化（16个段落）
```
【访谈者】比如说盖房子，或者孩子的教育等方面

【受访者】房子建起来了，孩子也长大了
```

### 减贫措施分析报告 ✨

```
📋 【减贫措施整体概述】
该地区通过住房保障、教育支持、就业帮扶、基础设施建设等措施，
显著改善了居民的生活条件。

👥 【受访者生活变化】
受访者家庭住房条件得到改善，子女教育水平提高，家庭经济状况改善。

📊 【具体减贫措施】

住房保障：
  • 建房
  • 改造

教育支持：
  • 子女教育资助
  • 子女高等教育支持

就业帮扶：
  • 外出务工机会
  • 技能培训

基础设施建设：
  • 道路改善
  • 水电设施改善

帮扶干部工作：
  • 第一书记定期走访，了解需求并提供帮助

⭐ 【工作亮点】
  1. 住房条件的显著改善
  2. 子女教育机会的增加
  3. 基础设施的改善
```

## ✨ 减贫措施分析功能

### 分析维度

系统自动从访谈内容中提取以下9个维度的减贫措施：

1. **住房保障** - 建房、改造、搬迁等
2. **教育支持** - 子女教育、助学金等
3. **医疗保障** - 医疗救助、健康帮扶等
4. **就业帮扶** - 外出务工、技能培训等
5. **产业扶贫** - 发展产业、种植养殖等
6. **基础设施建设** - 道路、水电、网络等
7. **社会保障** - 低保、养老、救助金等
8. **帮扶干部工作** - 驻村干部、第一书记工作
9. **其他措施** - 其他特色减贫措施

### 应用场景

- 📊 **快速汇总** - 批量提取几百个访谈的减贫措施
- 📈 **数据分析** - 统计各维度措施的实施频率
- 📝 **报告撰写** - 为研究报告提供结构化素材
- 🔍 **政策评估** - 评估不同地区的减贫政策效果

## ⚙️ 高级功能

### 断点续传

程序会自动检测已处理的文件，如果所有输出文件都存在，会跳过该文件：

```
⏭️  文件已处理，跳过: interview1.mp3
```

如需重新处理，删除对应的输出文件即可。

### 批量处理大量文件

处理几百个文件时，程序会：
- ✅ 自动限制请求频率，避免API限流
- ✅ 显示实时进度
- ✅ 出错后继续处理剩余文件
- ✅ 最后打印完整统计报告

### 后台运行（推荐）

对于大批量文件，可以使用nohup后台运行：

```bash
nohup python batch_processor.py -i mp3data --ai > process.log 2>&1 &

# 查看进度
tail -f process.log
```

### 成本估算

| 服务 | 价格 | 示例成本（100个10分钟访谈） |
|------|------|---------------------------|
| 讯飞转写 | ¥0.3-0.5/分钟 | ¥300-500 |
| 智谱AI | ¥0.001/千字 | ¥2-5 |
| **总计** | - | **¥302-505** |

## 🔧 故障排除

### 问题1: ModuleNotFoundError

```bash
# 确保安装了依赖
pip install zhipuai requests
```

### 问题2: API调用失败

检查 `config.py` 中的API密钥是否正确：
- 讯飞密钥获取: https://www.xfyun.cn/
- 智谱密钥获取: https://open.bigmodel.cn/

### 问题3: 转写结果为空

可能原因：
- 音频文件损坏
- 音频格式不支持（支持：mp3, wav, m4a, flac）
- 音频时长过长（建议<60分钟）

### 问题4: AI优化失败

检查智谱AI API密钥和余额：
- 登录 https://open.bigmodel.cn/ 查看账户余额
- 确认API密钥有效期

### 问题5: Python版本问题

确保使用 Python 3.6 或更高版本：

```bash
# 使用conda环境（推荐）
conda activate jianpin
python --version  # 应显示 Python 3.x

# 或直接指定Python路径
/opt/anaconda3/envs/jianpin/bin/python batch_processor.py -i mp3data --ai
```

## 💡 使用建议

### 1. 先测试单个文件

```bash
# 将一个测试音频放入test_dir文件夹
python batch_processor.py -i test_dir --ai
```

### 2. 分批处理大量文件

如果有几百个文件，建议分批处理：

```bash
# 处理第1-100个文件
python batch_processor.py -i batch1 --ai

# 处理第101-200个文件
python batch_processor.py -i batch2 --ai
```

### 3. 定期备份输出文件

```bash
# 备份output目录
cp -r output output_backup_$(date +%Y%m%d)
```

## 📊 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.6+ | 开发语言 |
| 讯飞语音转写API | 语音识别和说话人分离 |
| 智谱AI API | 文本优化和智能分析 |
| requests | HTTP请求 |

## 📝 依赖清单

```
requests>=2.31.0        # HTTP请求
zhipuai>=2.0.0          # 智谱AI SDK
python-dotenv>=1.0.0    # 环境变量管理（可选）
```

## 📞 技术支持

遇到问题请检查：
1. ✅ API密钥是否正确
2. ✅ 网络连接是否正常
3. ✅ Python版本是否>=3.6
4. ✅ 依赖包是否完整安装

## 🎯 版本历史

### v2.0.0 (2025-10-12) - 当前版本

**新增功能**：
- ✨ 减贫措施智能分析（9个维度）
- ✨ 结构化报告生成（TXT + JSON）
- ✨ 批量处理支持
- ✨ 断点续传功能

**优化改进**：
- 🚀 删除 WhisperX 后端，专注讯飞API
- 🚀 代码量减少47%（~1500行 → ~800行）
- 🚀 依赖包减少70%（~10个 → 3个）
- 🚀 配置文件简化53%

### v1.0.0 (初始版本)

**基础功能**：
- 讯飞API语音转写
- 文本合并优化
- 智谱AI文本清洗

---

**版本**: 2.0.0  
**更新日期**: 2025-10-12  
**作者**: 中国人民大学应用经济学院  
**许可**: MIT License

