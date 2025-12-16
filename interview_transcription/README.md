# 县域标签与减贫措施分析系统

基于智谱AI的县域标签生成和减贫措施分析工具，用于批量处理县域访谈数据，自动生成标准化标签和分析报告。

## 核心功能

### 1. 县域标签生成
- **单个县处理** (`county_labeler.py`): 为单个县生成标签和减贫措施分析
- **批量处理** (`process_all_counties.py`): 自动发现并批量处理所有县
- **标准化标签体系**: 固定格式的县域标签和措施标签，便于后续分析

### 2. 辅助工具
- **标签分析** (`analyze_tags.py`): 分析所有县的标签分布和模式
- **标签验证** (`validate_tags.py`): 验证标签是否符合标准化体系
- **文本合并** (`county_text_merger.py`): 合并县域访谈文本
- **基础信息获取** (`fetch_county_briefs.py`): 从高德地图API获取县域基础信息

## 快速开始

### 1. 安装依赖

```bash
cd interview_transcription
pip install python-dotenv zhipuai python-docx requests
```

### 2. 配置API密钥

**方式1：命令行环境变量（推荐）**

```bash
# 导出环境变量（当前终端会话有效）
export ZHIPU_API_KEY=your_api_key_here
export ZHIPU_MODEL=glm-4-flash

# 或直接在命令中设置
ZHIPU_API_KEY=your_api_key_here python3 county_labeler.py ...
```

**方式2：使用.env文件（可选）**

在 `interview_transcription` 目录下创建 `.env` 文件：

```bash
ZHIPU_API_KEY=your_api_key_here
ZHIPU_MODEL=glm-4-flash
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

### 3. 运行示例

**处理单个县**：

```bash
export ZHIPU_API_KEY=your_api_key_here

python3 county_labeler.py \
    --county-dir "input_text/河北省张家口市蔚县 （20240722-20240723）" \
    --text-dir "input_text/河北省张家口市蔚县 （20240722-20240723）/河北省张家口市蔚县 （20240722-20240723）文本"
```

**批量处理所有县**：

```bash
export ZHIPU_API_KEY=your_api_key_here

# 处理所有县
python3 process_all_counties.py

# 只处理前10个县（测试）
python3 process_all_counties.py --limit 10

# 强制重新处理所有县
python3 process_all_counties.py --force
```

## 项目结构

```
interview_transcription/
├── county_labeler.py          # 核心：单个县标签生成
├── process_all_counties.py    # 核心：批量处理所有县
├── fetch_county_briefs.py    # 获取县域基础信息（高德API）
├── analyze_tags.py            # 标签分析工具
├── validate_tags.py           # 标签验证工具
├── county_text_merger.py      # 文本合并工具
├── config.py                  # 配置文件
├── requirements.txt           # 依赖包列表
│
├── input_text/                # 输入数据（已忽略，不提交Git）
│   └── {县目录}/
│       ├── 基础信息.txt
│       └── {文本目录}/
│           └── *.docx
│
└── output/                    # 输出数据（已忽略，不提交Git）
    ├── 2_merged_texts/        # 合并后的文本
    └── 4_poverty_reduction_summary/  # 标签JSON文件
```

## 核心脚本说明

### county_labeler.py - 单个县标签生成

**功能**：
- 读取县域基础信息和访谈文本
- 使用智谱AI生成标准化标签
- 输出JSON格式的分析结果

**用法**：
```bash
python3 county_labeler.py \
    --county-dir "input_text/县目录" \
    --text-dir "input_text/县目录/文本目录" \
    --char-limit 50000
```

**参数**：
- `--county-dir`: 县目录路径（需包含基础信息.txt）
- `--text-dir`: 访谈文本目录（docx/txt文件）
- `--combined-file`: 如果已有合并好的文本文件，可直接指定
- `--char-limit`: 文本字符数限制（默认50000）
- `--output`: 自定义输出路径

**输出**：
- `output/4_poverty_reduction_summary/{县名}_labels.json`

### process_all_counties.py - 批量处理

**功能**：
- 自动扫描所有县目录
- 批量处理所有符合条件的县
- 生成处理日志和统计报告

**用法**：
```bash
python3 process_all_counties.py [选项]
```

**选项**：
- `--limit N`: 限制处理的县数量（测试用）
- `--force`: 强制重新处理所有县
- `--dry-run`: 只检查，不实际处理
- `--char-limit N`: 文本字符数限制（默认50000）
- `--log PATH`: 自定义日志文件路径

**输出**：
- 每个县的标签JSON文件
- `output/batch_processing_log.txt` - 处理日志

### fetch_county_briefs.py - 获取县域基础信息

**功能**：
- 使用高德地图API获取县域基础信息
- 生成 `基础信息.txt` 文件

**用法**：
```bash
# 需要设置高德API密钥
export AMAP_KEY=your_amap_key_here

# 处理所有县
python3 fetch_county_briefs.py

# 只处理前5个县
python3 fetch_county_briefs.py --limit 5

# 覆盖已有文件
python3 fetch_county_briefs.py --overwrite
```

### analyze_tags.py - 标签分析

**功能**：
- 分析所有县的标签分布
- 生成标签统计报告
- 生成标签映射表

**用法**：
```bash
python3 analyze_tags.py
```

**输出**：
- `output/tag_analysis_report.txt` - 分析报告
- `output/tag_mapping.json` - 标签映射表

### validate_tags.py - 标签验证

**功能**：
- 验证所有标签是否符合标准化体系
- 识别非标准标签
- 生成验证报告

**用法**：
```bash
python3 validate_tags.py
```

**输出**：
- `output/tag_validation_report.json` - 验证报告

## 标准化标签体系

### 县域标签（3-6个）

**必选（1个）**：地形特征
- 山区县、高原县、平原县、丘陵县、盆地县、河谷县

**可选（0-2个）**：区位特征
- 革命老区县、民族聚居县、边境县、易地搬迁重点县、生态脆弱区、资源型县

**可选（0-2个）**：产业特征
- 农业大县、特色产业县、旅游县、电商县、光伏县、养殖县、种植县

**可选（0-1个）**：政策特征
- 东西部协作重点县、定点帮扶县、示范县

### 措施标签（4-10个）

共12个类别，62个标准标签：
- 产业扶贫（6个）
- 基础设施（6个）
- 教育扶贫（6个）
- 医疗扶贫（5个）
- 就业扶贫（5个）
- 易地搬迁（3个）
- 社会保障（5个）
- 金融支持（4个）
- 组织保障（5个）
- 机制创新（5个）
- 协作帮扶（4个）
- 其他（4个）

详细列表见代码中的 `PROMPT_TEMPLATE`。

## 输出格式

每个县的标签文件格式（JSON）：

```json
{
  "county_name": "县名",
  "county_tags": ["山区县", "革命老区县", "农业大县"],
  "effective_measures": [
    {
      "tag": "产业扶贫",
      "evidence": "通过发展特色产业带动增收"
    },
    {
      "tag": "基础设施建设",
      "evidence": "完成道路、饮水等基础设施改造"
    }
  ],
  "summary": "2-3句总结"
}
```

## 环境变量说明

### 必需
- `ZHIPU_API_KEY` - 智谱AI API密钥

### 可选
- `ZHIPU_MODEL` - 模型名称（默认：glm-4-flash）
- `ZHIPU_BASE_URL` - API基础URL（默认：https://open.bigmodel.cn/api/paas/v4）
- `AMAP_KEY` - 高德地图API密钥（用于fetch_county_briefs.py）

## 常见问题

### Q1: 提示 "缺少 ZHIPU_API_KEY"

**解决**：设置环境变量
```bash
export ZHIPU_API_KEY=your_api_key_here
```

### Q2: 提示 "未找到基础信息.txt"

**解决**：确保县目录下有 `基础信息.txt` 文件，或使用 `fetch_county_briefs.py` 生成

### Q3: 提示 "未找到文本目录"

**解决**：检查文本目录命名是否符合以下模式：
- `{县名}-文本`
- `{县名}文本`
- `{县名} 文本`（有空格）

### Q4: 处理速度慢

**解决**：
- 降低 `--char-limit` 值（如30000）
- 批量处理脚本已内置延迟，避免API调用过快

## 注意事项

1. **API密钥安全**：
   - ✅ 使用命令行环境变量方式，密钥不会保存到文件
   - ✅ `.env` 文件已被添加到 `.gitignore`
   - ✅ 不要将API密钥硬编码到代码中

2. **数据文件**：
   - ✅ `input_text/` 和 `output/` 目录已被忽略
   - ✅ 这些目录中的文件不会被提交到Git

3. **网络要求**：
   - 需要网络连接以调用智谱AI API
   - 如果使用代理，确保正确配置

4. **处理时间**：
   - 单个县处理时间：约30秒-2分钟
   - 批量处理127个县：约1-2小时（取决于网络和API响应速度）

## 依赖包

```
python-dotenv>=1.0.0    # 环境变量管理（可选）
zhipuai>=2.0.0          # 智谱AI SDK
python-docx>=1.0.0      # Word文档处理
requests>=2.31.0        # HTTP请求
```

安装：
```bash
pip install -r requirements.txt
```

## 版本历史

### v2.0.0 (当前版本)
- ✨ 标准化标签体系
- ✨ 批量处理功能
- ✨ 标签分析和验证工具
- ✨ 命令行环境变量支持

---

**版本**: 2.0.0  
**更新日期**: 2025-01  
**作者**: 中国人民大学应用经济学院
