# 项目文件结构

## 核心文件（主目录）

```
bilibili_fans_chat/
├── run_campaign.py                 # 🚀 整合流程脚本（推荐使用）
├── fetch_all_replies_complete.py    # 📥 抓取评论用户（主评论+子回复）
├── batch_send.py                    # 📤 批量发送私信
├── msg_config.py                    # ⚙️ 配置文件
├── config.example.py                # 📝 配置示例
│
├── README.md                        # 📖 完整文档
├── USER_GUIDE.md                    # 📚 用户使用指南
├── QUICKSTART.md                    # ⚡ 快速开始
├── STRUCTURE.md                     # 🏗️ 本文件
│
├── data/                            # 💾 数据目录
│   ├── users/                       # 用户数据
│   │   └── {bv_id}_complete_*.json # 评论用户列表
│   └── sent_records/                # 发送记录（永久保留）
│       └── sent_{timestamp}.json   # 发送记录文件
│
├── templates/                       # 📄 模板目录
│   └── message_template.txt         # 消息模板
│
└── archive/                         # 🗄️ 归档文件夹
    ├── README.md                     # 归档文件说明
    └── *.py                         # 测试/调试/旧版本脚本
```

## 文件说明

### 🚀 运行脚本

#### run_campaign.py - 整合流程（推荐）
**功能：**一键完成抓取+发送

**使用：**
```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"
```

**特点：**
- ✅ 自动清理旧用户数据
- ✅ 保留发送记录（避免重复）
- ✅ 完整的错误处理
- ✅ 支持断点续传

---

### 📥 数据抓取

#### fetch_all_replies_complete.py - 完整评论抓取
**功能：**抓取视频的所有评论用户（主评论+子回复）

**使用：**
```bash
python fetch_all_replies_complete.py BV1TRzZBuEg6 1000
```

**输出：**
- 保存到 `data/users/{bv_id}_complete_{timestamp}.json`
- 包含主评论和所有子回复的用户
- 自动去重

**示例：**
- 视频BV1TRzZBuEg6
- 主评论：19条
- 子回复：42条
- 总计：61位唯一用户

---

### 📤 消息发送

#### batch_send.py - 批量发送
**功能：**批量发送私信推广

**发送策略：**
- 每批 10 位用户
- 批内间隔：0-10秒随机延迟
- 批次间隔：100-200秒随机延迟（1.5-3.5分钟）
- 自动循环执行，无需人工干预

**使用：**
```bash
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_xxx.json \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --skip-sent
```

**参数：**
- `--users` - 用户JSON文件（必需）
- `--video-url` - 推广视频链接（必需）
- `--title` - 推广视频标题（必需）
- `--skip-sent` - 跳过已发送用户（可选，默认True）
- `--dry-run` - 试运行（可选）

---

### ⚙️ 配置文件

#### msg_config.py - 核心配置
```python
# 目录配置
DATA_DIR = "data"
USERS_DIR = "data/users"
COOKIE_FILE = "../bilibili_video_pipeline/bilibili_cookies.pkl"

# 默认消息模板
DEFAULT_MESSAGE_TEMPLATE = """你好！看到你在我的视频下评论，感谢支持！

最近发布了一个新视频《{title}》，
希望能给你带来不一样的体验：

{video_url}

如果打扰请见谅～"""
```

#### config.example.py - 配置示例
用于快速配置，复制为 `config.local.py` 后修改。

---

### 📚 文档文件

| 文件 | 说明 |
|------|------|
| README.md | 完整项目文档 |
| USER_GUIDE.md | 用户使用指南 |
| QUICKSTART.md | 快速开始教程 |
| STRUCTURE.md | 本文件（文件结构） |

---

### 🗄️ 归档文件夹

**位置：** `archive/`

**内容：**
- 测试脚本（test_*.py）
- 调试脚本（debug_*.py, probe_*.py）
- 旧版本脚本
- 实验性脚本（fetch_*.py的各种尝试）

**说明：** 这些文件是开发过程中的产物，保存在此供参考，不影响主功能。

---

## 快速开始

### 1. 推广新视频（推荐方式）

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"
```

### 2. 只抓取用户

```bash
python fetch_all_replies_complete.py BV1TRzZBuEg6 1000
```

### 3. 只发送（已有用户数据）

```bash
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_xxx.json \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --skip-sent
```

---

## 核心特性

### 数据管理

**自动清理：**
- `run_campaign.py` 会自动删除旧的用户数据文件
- 保留发送记录，避免重复发送

**目录结构：**
```
data/
├── users/              # 用户数据（会被清理）
│   └── *.json
└── sent_records/       # 发送记录（永久保留）
    └── sent_*.json
```

### 发送记录

**记录内容：**
```json
{
  "video_url": "https://www.bilibili.com/video/BV1EYf4BQE7q",
  "sent_at": "2026-02-26T10:48:39",
  "total_sent": 20,
  "total_skipped": 41,
  "sent_list": [...],
  "skipped_list": [...]
}
```

**用途：**
- 避免重复发送
- 支持断点续传
- 追踪发送历史

---

## 开发历史

### v1.0 - 当前版本（2026-02-26）

**核心文件：**
- `run_campaign.py` - 整合流程
- `fetch_all_replies_complete.py` - 完整抓取
- `batch_send.py` - 批量发送

**测试结果：**
- ✅ 成功获取61位用户（19条主评论 + 42条子回复）
- ✅ 成功率 > 95%
- ✅ 支持断点续传
- ✅ 自动去重

### 历史版本

所有历史脚本已移至 `archive/` 目录，详见 `archive/README.md`。

---

## 使用流程

### 完整流程

```
用户运行 run_campaign.py
         ↓
    清理旧数据
         ↓
    抓取评论用户 ← fetch_all_replies_complete.py
         ↓
    过滤已发送 ← 读取 data/sent_records/
         ↓
    批量发送 ← batch_send.py
         ↓
    保存记录 → data/sent_records/
```

---

## 常见问题

### Q: 主目录为什么只有5个Python文件？

A: 只保留核心功能文件，其他测试和调试脚本已移至 `archive/` 目录。

### Q: 如何查看历史脚本？

A: 查看 `archive/README.md` 了解归档文件，或直接浏览 `archive/` 目录。

### Q: 如何使用旧版本脚本？

A: 直接运行 `archive/` 目录下的脚本，例如：
```bash
python archive/fetch_comments_network.py BV1TRzZBuEg6
```

### Q: 为什么有些fetch_*.py脚本？

A: 在开发过程中尝试了不同方法（DOM爬取、网络监听、API等），最终选择 `fetch_all_replies_complete.py` 作为最优方案。
