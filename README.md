# B站私信推广工具

自动获取B站视频评论用户，批量发送私信推广新视频。

## ⭐ 新功能: MediaCrawler集成

**重要更新**: 已集成 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler),获取用户数量提升 **3.5倍**!

### 效果对比

| 方案 | 60万播放视频获取用户数 | 提升 |
|------|---------------------|------|
| 原API方案 | 131位 | 基准 |
| **MediaCrawler** | **463位** | **+253%** ⬆️ |

### 快速使用MediaCrawler

```bash
# 方式1: 一键运行(自动使用MediaCrawler)
python run_campaign.py BV1hf4y1L763 \
  --video-url "https://www.bilibili.com/video/BV1TRzZBuEg6/" \
  --title "热河" \
  --keep-users

# 方式2: 使用已有数据
python quick_test_send.py

# 方式3: 手动运行MediaCrawler
cd MediaCrawler
python main.py --platform bili --lt qrcode --type detail
cd ..
python convert_media_crawler_data.py
```

**详细信息**: 查看 [MEDIACRAWLER_GUIDE.md](MEDIACRAWLER_GUIDE.md) 和 [MEDIACRAWLER_REPORT.md](MEDIACRAWLER_REPORT.md)

---

## 🚀 快速开始

### 一键运行（推荐）

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"
```

这个命令会自动完成：
1. ✅ 删除旧的用户数据文件
2. ✅ 保留发送记录（避免重复发送）
3. ✅ 从 BV1TRzZBuEg6 抓取评论用户（主评论+子回复）
4. ✅ 发送私信给所有用户（自动跳过已发送的）
5. ✅ 保存新的发送记录

**完整使用流程详见：[QUICKSTART.md](QUICKSTART.md)**

---

## ⚠️ 重要提示

### 风险警告
1. **B站限制**：非互关用户可能只能发送1条消息
2. **频率限制**：短期大量发送可能触发风控
3. **账号风险**：异常行为可能导致账号限制或封禁
4. **合规使用**：仅用于正常推广，不发送垃圾信息

### 使用建议
- 首次使用先小规模测试（5-10条）
- 监控账号状态，观察是否有警告
- 使用保守模式确保安全
- 准备备用账号以备不时之需

---

## 功能特性

### 核心功能
- ✅ 自动获取视频评论用户（主评论+子回复）
- ✅ 批量发送私信推广
- ✅ 发送记录管理（避免重复发送）
- ✅ 外部视频链接支持
- ✅ 自定义消息模板
- ✅ 进度实时显示

### 安全特性
- 🛡️ 批量发送模式：每批10位用户
- 🛡️ 批内间隔：0-10秒随机延迟
- 🛡️ 批次间隔：100-200秒随机延迟（1.5-3.5分钟）
- 🛡️ 人性化行为：模拟真实用户发送模式
- 🛡️ 自动跳过限制用户
- 🛡️ **实时记录**：每条发送后立即保存，防止数据丢失
- 🛡️ 发送记录持久化

---

## 文件结构

```
bilibili_fans_chat/
├── MediaCrawler/                    # MediaCrawler爬虫工具 ⭐ 新增
│   ├── config/                      # 配置文件
│   ├── data/bili/json/              # 爬取的原始数据
│   └── main.py                      # MediaCrawler主程序
├── fetch_all_replies_complete.py   # 获取所有评论用户（主评论+子回复）
├── batch_send.py                    # 批量发送私信（优化版）
├── run_campaign.py                  # 完整流程脚本（支持MediaCrawler）
├── quick_test_send.py               # 快速测试脚本 ⭐ 新增
├── convert_media_crawler_data.py    # MediaCrawler数据转换工具 ⭐ 新增
├── msg_config.py                    # 配置文件
├── requirements.txt                 # 依赖包
├── README.md                        # 本文档
├── MEDIACRAWLER_GUIDE.md            # MediaCrawler使用指南 ⭐ 新增
├── MEDIACRAWLER_REPORT.md           # MediaCrawler测试报告 ⭐ 新增
├── TROUBLESHOOTING.md               # 问题诊断文档 ⭐ 新增
├── data/                            # 数据目录
│   ├── users/                       # 用户数据
│   │   ├── {bv_id}_complete_{timestamp}.json     # API方案数据
│   │   └── {bv_id}_mediacrawler_{timestamp}.json # MediaCrawler数据
│   └── sent_records/                # 发送记录
│       └── sent_{timestamp}.json    # 发送记录文件
└── templates/
    └── message_template.txt         # 消息模板
```

---

## 安装

### 1. 安装依赖

```bash
cd bilibili_fans_chat
pip install -r requirements.txt
```

### 2. 配置Cookies

**重要**：需要先使用 `bilibili_video_pipeline` 登录B站获取cookies。

cookies文件位置：
```
../bilibili_video_pipeline/bilibili_cookies.pkl
```

程序会自动读取此文件。

---

## 使用方法

### 方案选择

**推荐: 使用MediaCrawler** (获取3.5倍用户)
- ✅ 适用于高播放量视频(>10万)
- ✅ 突破B站API限制
- ✅ 数据更全面
- ⚠️ 首次需扫码登录

**备选: 使用原API方案** (快速测试)
- ✅ 快速方便
- ✅ 无需额外配置
- ❌ 受API限制,用户数量较少

### 方案A: 使用MediaCrawler (推荐)

#### 方式1: 自动运行(最简单)

```bash
# 自动使用MediaCrawler爬取并发送
python run_campaign.py BV1hf4y1L763 \
  --video-url "https://www.bilibili.com/video/BV1TRzZBuEg6/" \
  --title "热河" \
  --keep-users
```

首次运行时会:
1. 检测到没有MediaCrawler数据
2. 询问是否运行MediaCrawler
3. 自动打开浏览器并显示二维码
4. 用B站App扫码登录
5. 自动爬取并转换数据
6. 开始发送私信

#### 方式2: 使用已有数据

如果已经运行过MediaCrawler,直接使用:

```bash
python quick_test_send.py
```

会自动检测并使用最新的MediaCrawler数据。

#### 方式3: 手动运行

```bash
# 1. 配置视频BV号
# 编辑 MediaCrawler/config/bilibili_config.py
BILI_SPECIFIED_ID_LIST = ["BV1hf4y1L763"]

# 2. 运行MediaCrawler(首次需扫码登录)
cd MediaCrawler
python main.py --platform bili --lt qrcode --type detail

# 3. 转换数据
cd ..
python convert_media_crawler_data.py

# 4. 发送私信
python batch_send.py \
  --users data/users/BV1hf4y1L763_mediacrawler_*.json \
  --video-url "https://www.bilibili.com/video/BV1TRzZBuEg6/" \
  --title "热河"
```

### 方案B: 使用原API方案

### 步骤1：获取评论用户

使用完整爬虫获取视频的所有评论用户（包括主评论和子回复）：

```bash
# 获取指定视频的所有评论用户
python fetch_all_replies_complete.py BV1TRzZBuEg6 1000

# 参数说明：
# - BV1TRzZBuEg6: 视频BV号
# - 1000: 最多获取用户数（可选，默认1000）
```

**输出：**
- 在 `data/users/` 目录生成用户JSON文件
- 包含主评论和所有子回复的用户
- 自动去重，确保用户唯一性

**示例输出：**
```
[爬虫] 完整获取所有评论用户
[视频] BV1TRzZBuEg6
[目标] 最多获取 1000 位用户

[步骤1] 获取aid...
[成功] AV115976314032580

[步骤3] 获取主评论...
[1/19] 健美疯 (子回复: 24)
       [2] 针眼画师oO
       [3] 四叠半嘴角上扬Reveッ
       ...

[完成] 共获取 61 位用户
[保存] data/users/BV1TRzZBuEg6_complete_20260226_104839.json
```

### 步骤2：批量发送私信

使用获取的用户列表批量发送私信：

```bash
# 基本用法
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_20260226_104839.json \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"

# 跳过已发送用户（仅检查当前视频）
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_20260226_104839.json \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --skip-sent

# 试运行（不实际发送）
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_20260226_104839.json \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --dry-run
```

### 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--users` | ✅ | 用户JSON文件路径 | `data/users/xxx.json` |
| `--video-url` | ✅ | 推广视频链接 | `https://www.bilibili.com/video/BV1xxx` |
| `--title` | ❌ | 视频标题（用于消息模板） | `--title "我的视频"` |
| `--skip-sent` | ❌ | 跳过已发送用户（仅当前视频） | `--skip-sent` |
| `--dry-run` | ❌ | 试运行，不实际发送 | `--dry-run` |

### 批量发送策略

程序采用**自动批量发送模式**，无需人工干预：

**发送规则：**
- 每批 **10 位用户**
- 批内用户间隔：**0-10秒** 随机延迟
- 批次间隔：**100-200秒**（1.5-3.5分钟）随机延迟
- 循环发送直到全部完成

**执行流程：**
```
批次 1/7 (10位用户)
  [1/61] 用户A → 等待3秒
  [2/61] 用户B → 等待7秒
  ...
  [10/61] 用户J
  [批次完成] 等待156秒后继续下一批次... (预计 14:23:45 继续)

批次 2/7 (10位用户)
  [11/61] 用户K → 等待2秒
  ...

...循环直到所有用户发送完成
```

**优势：**
- ✅ 无需人工确认，全自动执行
- ✅ 批次间隔避免触发频率限制
- ✅ 实时显示进度和预计完成时间
- ✅ 适合大规模发送（如60+用户）

---

## 消息模板

### 修改模板

编辑 `templates/message_template.txt`：

```
你好！看到你在我的视频下评论，感谢支持！

最近发布了一个新视频《{title}》，
希望能给你带来不一样的体验：

{video_url}

如果打扰请见谅～
```

### 模板变量

- `{title}` - 视频标题（通过 `--title` 参数指定）
- `{video_url}` - 视频链接（通过 `--video-url` 参数提供）

---

## 发送记录管理

### 实时记录机制

**重要特性：** 程序采用**实时记录**机制，每次发送后立即保存到文件！

**优势：**
- ✅ 防止程序中断导致数据丢失
- ✅ 支持随时中断续传
- ✅ 每条记录都有准确的时间戳
- ✅ 可实时查看发送进度

### 记录文件格式

发送开始时立即创建记录文件：`data/sent_records/sent_YYYYMMDD_HHMMSS.json`

```json
{
  "video_url": "https://www.bilibili.com/video/BV1EYf4BQE7q",
  "started_at": "2026-02-26T14:20:15.123456",
  "updated_at": "2026-02-26T14:35:22.654321",
  "completed_at": "2026-02-26T14:35:22.654321",
  "total_users": 61,
  "total_sent": 50,
  "total_skipped": 9,
  "total_failed": 2,
  "sent_list": [
    {
      "user_id": "53282989",
      "nickname": "健美疯",
      "sent_at": "2026-02-26T14:21:30.456789"
    }
  ],
  "skipped_list": [
    {
      "user_id": "123456",
      "nickname": "已发送用户",
      "reason": "已发送过（跳过）"
    }
  ],
  "failed_list": [
    {
      "user_id": "789012",
      "nickname": "失败用户",
      "reason": "未找到contenteditable输入框",
      "sent_at": "2026-02-26T14:30:10.123456"
    }
  ]
}
```

**时间戳说明：**
- `started_at` - 开始发送时间
- `updated_at` - 最后更新时间（每次追加记录时更新）
- `completed_at` - 完成时间（全部发送完成后添加）
- `sent_at` - 单条记录的发送时间

### 避免重复发送

使用 `--skip-sent` 参数自动跳过已发送的用户：

```bash
python batch_send.py \
  --users data/users/xxx.json \
  --video-url "https://www.bilibili.com/video/BV1xxx" \
  --skip-sent
```

程序会：
1. 检查 `data/sent_records/` 目录
2. 加载所有发送记录
3. 过滤掉已发送给该视频的用户
4. 只发送给新用户

---

## 数据文件格式

### 用户列表文件

```json
{
  "bv_id": "BV1TRzZBuEg6",
  "aid": 115976314032580,
  "fetched_at": "2026-02-26T10:48:39.525144",
  "total_users": 61,
  "users": [
    {
      "user_id": "53282989",
      "nickname": "健美疯",
      "comment": "完了 这歌有点火了 大家低调点[笑哭]"
    },
    {
      "user_id": "294676365",
      "nickname": "针眼画师oO",
      "comment": "现在好像放开了一点..."
    }
  ]
}
```

---

## 发送策略

### 保守模式（默认）

**参数配置：**
- 每条间隔：10-20秒（随机）
- 每次成功后手动确认是否继续
- 自动跳过限制用户

**示例耗时：**
- 10条用户：约5-10分钟
- 50条用户：约30-60分钟

### 速率控制逻辑

```python
# 1. 基础间隔
每条消息间隔 10-20 秒（随机）

# 2. 手动确认
每成功发送1条后 → 询问是否继续

# 3. 自动跳过
用户限制私信 → 自动跳过

# 4. 发送记录
自动记录已发送用户 → 支持断点续传
```

---

## 完整使用流程

### 场景：推广新视频到所有评论用户

```bash
# 步骤1：获取评论用户（假设从视频BV1TRzZBuEg6获取）
python fetch_all_replies_complete.py BV1TRzZBuEg6 1000

# 输出示例：
# [完成] 共获取 61 位用户
# [保存] data/users/BV1TRzZBuEg6_complete_20260226_104839.json

# 步骤2：第一次发送（发送给新视频 BV1EYf4BQE7q）
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_20260226_104839.json \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"

# 假设发送了20条后手动停止

# 步骤3：第二次发送（继续发送剩余用户，自动跳过已发送的）
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_20260226_104839.json \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --skip-sent

# 程序会自动跳过已发送的20条，继续发送剩余41条
```

---

## 常见问题

### 0. MediaCrawler相关问题 ⭐

**Q: 为什么推荐使用MediaCrawler?**
A: MediaCrawler可以获取3.5倍的用户数量(463位 vs 131位),特别适合高播放量视频。

**Q: MediaCrawler首次使用需要什么?**
A:
1. 首次需要扫码登录(20秒内用B站App扫描二维码)
2. 之后会缓存登录状态,无需重复登录
3. 需要安装Chromium浏览器驱动(约135MB)

**Q: 如何选择使用哪种方案?**
A:
- **高播放量视频(>10万)** → 使用MediaCrawler
- **快速测试** → 使用原API方案(加 `--use-api` 参数)

**Q: run_campaign.py会自动使用MediaCrawler吗?**
A: 是的!新版 `run_campaign.py` 会:
1. 自动检测MediaCrawler数据
2. 如果存在,询问是否使用
3. 如果不存在,询问是否运行MediaCrawler

**Q: 为什么只有131位用户,应该有更多?**
A: 可能使用了原API方案。解决方法:
```bash
# 方式1: 使用快速测试
python quick_test_send.py

# 方式2: 强制使用MediaCrawler数据
python run_campaign.py BV1hf4y1L763 \
  --video-url "..." \
  --title "..." \
  --keep-users
```

详细说明: 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 1. 获取到的用户数量不对

**问题**：只获取到19位用户，但视频有更多评论

**原因**：19条是主评论，需要获取子回复

**解决**：使用 `fetch_all_replies_complete.py` 脚本，它会获取：
- 所有主评论
- 所有子回复
- 自动去重

**示例**：
```
主评论: 19条
子回复: 42条
总计: 61位唯一用户
```

### 2. Cookies加载失败

**问题**：`[错误] Cookies文件不存在`

**解决**：
1. 先使用 `bilibili_video_pipeline` 登录B站
2. 确保 `bilibili_cookies.pkl` 文件存在
3. 检查文件路径是否正确

### 3. 大量用户被跳过

**问题**：很多用户显示"跳过"

**原因**：
- 使用了 `--skip-sent` 参数
- 这些用户在之前的发送中已经发送过

**说明**：这是正常的去重机制

### 4. 发送速度太慢

**问题**：发送速度太慢

**说明**：
- 这是保守模式的安全策略
- 每条间隔10-20秒
- 每次成功后需手动确认
- 避免触发B站风控

### 5. 如何查看已发送用户

**方法1**：查看记录文件
```bash
# 查看最新的发送记录
ls -lt data/sent_records/ | head -5
cat data/sent_records/sent_xxx.json
```

**方法2**：使用 `--skip-sent` 查看统计
```bash
python batch_send.py \
  --users data/users/xxx.json \
  --video-url "https://..." \
  --skip-sent

# 会显示：[记录] 已发送记录: XX 位用户
```

---

## 测试建议

### 首次测试

```bash
# 1. 获取用户列表
python fetch_all_replies_complete.py BV1TRzZBuEg6 1000

# 2. 试运行（不实际发送）
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_xxx.json \
  --video-url "https://www.bilibili.com/video/BV1xxx" \
  --title "测试视频" \
  --dry-run

# 3. 小规模测试（手动停止）
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_xxx.json \
  --video-url "https://www.bilibili.com/video/BV1xxx" \
  --title "测试视频"

# 发送几条后手动停止，观察结果

# 4. 检查发送记录
cat data/sent_records/sent_xxx.json

# 5. 如果正常，继续发送
python batch_send.py \
  --users data/users/BV1TRzZBuEg6_complete_xxx.json \
  --video-url "https://www.bilibili.com/video/BV1xxx" \
  --title "正式视频" \
  --skip-sent
```

### 监控指标

- ✅ 发送成功率 > 80%
- ✅ 账号状态正常
- ✅ 无B站警告
- ✅ 用户无投诉

---

## 配置说明

### 修改配置

编辑 `msg_config.py` 文件：

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

---

## 故障排除

### 程序崩溃

**检查**：
1. 查看错误信息
2. 检查网络连接
3. 检查浏览器驱动

**恢复**：
- 发送记录已保存在 `data/sent_records/`
- 使用 `--skip-sent` 继续发送剩余用户

### 浏览器问题

**问题**：浏览器无法启动

**解决**：
```bash
# 重新安装ChromeDriver
pip install --upgrade webdriver-manager
```

---

## 技术实现

### 获取评论用户

**文件**：`fetch_all_replies_complete.py`

**实现原理**：
1. 通过API获取视频aid
2. 获取主评论列表
3. 遍历每条主评论，获取其所有子回复（分页）
4. 去重合并用户
5. 保存到JSON文件

**关键点**：
- 子回复需要分页获取（每页20条）
- 通过用户ID去重
- 支持最多1000位用户

### 批量发送

**文件**：`batch_send.py`

**实现原理**：
1. 加载用户列表
2. 加载历史发送记录（如果使用 `--skip-sent`）
3. 过滤已发送用户
4. 逐个发送私信
5. 保存发送记录

**发送机制**：
- 使用 contenteditable 元素输入
- 模拟真实用户行为
- 随机延迟（10-20秒）
- 手动确认是否继续

---

## 开发历史

### v2.0 (2026-02-26) - MediaCrawler集成 ⭐

**重大更新**: 集成MediaCrawler,获取用户数量提升3.5倍!

**新增功能**：
- ✅ 集成MediaCrawler爬虫工具
- ✅ 数据格式自动转换
- ✅ 智能方案选择(MediaCrawler优先)
- ✅ 快速测试脚本(`quick_test_send.py`)
- ✅ 完整文档和测试报告

**新增文件**：
- `MediaCrawler/` - MediaCrawler爬虫工具
- `quick_test_send.py` - 快速测试脚本
- `convert_media_crawler_data.py` - 数据转换工具
- `MEDIACRAWLER_GUIDE.md` - 使用指南
- `MEDIACRAWLER_REPORT.md` - 测试报告
- `TROUBLESHOOTING.md` - 问题诊断

**测试结果**：
- 视频BV1hf4y1L763(60万播放):
  - 原API方案: 131位用户
  - MediaCrawler: 463位用户
  - **提升: +253%**

### v1.0 (2026-02-26)

**功能**：
- ✅ 完整评论用户获取（主评论+子回复）
- ✅ 批量发送私信
- ✅ 发送记录管理
- ✅ 外部视频链接支持
- ✅ 去重机制

**测试结果**：
- 视频BV1TRzZBuEg6：成功获取61位唯一用户
  - 主评论：19条
  - 子回复：42条
- 成功发送率：>95%

---

## 许可证

MIT License

---

## 免责声明

本工具仅供学习和正常推广使用。使用本工具造成的任何后果（包括但不限于账号封禁、法律纠纷等），由使用者自行承担。开发者不对使用本工具造成的任何损失负责。

请遵守B站用户协议和相关法律法规。
