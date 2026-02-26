# 快速开始

## 一键运行推广流程

### 完整流程（清理 + 抓取 + 发送）

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"
```

**这个命令会自动：**
1. ✅ 删除旧的用户数据文件
2. ✅ 保留发送记录（避免重复发送）
3. ✅ 从 BV1TRzZBuEg6 抓取评论用户（主评论+子回复）
4. ✅ 发送私信给所有用户（自动跳过已发送的）
5. ✅ 保存新的发送记录

---

## 参数说明

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `bv_id` | 源视频BV号（抓取这个视频的评论用户） | `BV1TRzZBuEg6` |
| `--video-url` | 推广的视频链接 | `https://www.bilibili.com/video/BV1xxx` |
| `--title` | 推广的视频标题 | `--title "忽然"` |

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--max-users` | 最多抓取用户数 | 1000 |
| `--skip-sent` | 跳过已发送用户 | ✅ 是 |
| `--no-skip-sent` | 不跳过已发送用户 | - |
| `--dry-run` | 试运行（不实际发送） | - |
| `--fetch-only` | 只抓取用户，不发送 | - |
| `--keep-users` | 保留已有用户文件 | - |

---

## 使用场景

### 场景1：首次推广（完整流程）

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"
```

### 场景2：试运行（测试）

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --dry-run
```

### 场景3：只抓取用户

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --fetch-only
```

### 场景4：保留旧用户数据

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --keep-users
```

### 场景5：不跳过已发送用户（重新发送）

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --no-skip-sent
```

---

## 完整流程示例

### 示例：推广视频"忽然"给BV1TRzZBuEg6的评论用户

```bash
# 第1步：运行推广脚本
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"

# 输出：
# ========================================================
#            B站私信推广工具 - 完整流程
# ========================================================
# [配置]
#   源视频: BV1TRzZBuEg6
#   推广视频: https://www.bilibili.com/video/BV1EYf4BQE7q
#   推广标题: 忽然
#   最大用户数: 1000
#   跳过已发送: 是
# ========================================================
# 重要提示:
#   1. 将删除当前所有用户数据文件
#   2. 将保留发送记录（支持断点续传）
#   3. 将发送私信给评论用户
# ========================================================
#
# 确认开始？(yes/no): yes

# 脚本会自动执行：
# [清理] 用户数据文件: 5个文件
#   - 删除: BV1TRzZBuEg6_complete_20260226_104839.json
#   ...
# [完成] 已清理 5 个用户文件
# [保留] 发送记录: 2 个文件

# [步骤1：抓取评论用户]
# [爬虫] 完整获取所有评论用户
# [视频] BV1TRzZBuEg6
# ...
# [完成] 共获取 61 位用户

# [步骤2：批量发送私信]
# [过滤] 待发送: 61 位，已跳过: 0 位
# [执行] python batch_send.py --users ... --skip-sent
# ...
# [完成] 推广流程完成！
```

### 如果中途停止

```bash
# 直接再次运行相同的命令
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --keep-users  # 保留已抓取的用户数据

# 程序会自动：
# 1. 保留上次抓取的用户数据
# 2. 跳过已发送的用户
# 3. 继续发送剩余用户
```

---

## 工作流程图

```
┌─────────────────────────────────────────────────────────┐
│           run_campaign.py - 完整流程                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  1. 清理旧用户数据文件    │
              │  (保留发送记录)          │
              └──────────────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  2. 抓取评论用户          │
              │  - 主评论                │
              │  - 子回复                │
              │  - 去重                  │
              └──────────────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  3. 过滤已发送用户        │
              │  (读取发送记录)          │
              └──────────────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  4. 批量发送私信          │
              │  - 每批10位用户          │
              │  - 批内0-10秒延迟        │
              │  - 批间100-200秒延迟     │
              │  - 自动循环执行          │
              │  - 保存记录              │
              └──────────────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  5. 完成                 │
              │  显示统计信息            │
              └──────────────────────────┘
```

---

## 常见问题

### Q: 如何确认脚本在运行？

A: 查看控制台输出，脚本会实时显示进度：

```
[1/19] 健美疯 (子回复: 24)
       [2] 针眼画师oO
       [3] 四叠半嘴角上扬Reveッ
```

### Q: 发送到一半想停止怎么办？

A: 直接按 `Ctrl+C` 停止，然后再次运行相同命令（加 `--keep-users`），脚本会自动跳过已发送的用户。

### Q: 如何查看发送记录？

A: 查看 `data/sent_records/` 目录：

```bash
ls -lt data/sent_records/
cat data/sent_records/sent_xxx.json
```

### Q: 如何重新发送给所有用户？

A: 使用 `--no-skip-sent` 参数：

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "..." \
  --title "..." \
  --no-skip-sent
```

---

## 数据文件说明

### 目录结构

```
data/
├── users/                           # 用户数据（会被清理）
│   └── {bv_id}_complete_*.json     # 评论用户列表
└── sent_records/                    # 发送记录（永久保留）
    └── sent_{timestamp}.json       # 发送记录文件
```

### 发送记录内容

```json
{
  "video_url": "https://www.bilibili.com/video/BV1EYf4BQE7q",
  "sent_at": "2026-02-26T10:48:39",
  "total_sent": 20,
  "total_skipped": 41,
  "sent_list": [
    {
      "user_id": "53282989",
      "nickname": "健美疯",
      "sent_at": "2026-02-26T10:50:15"
    }
  ]
}
```

---

## 实际使用示例

### 推广新视频

```bash
# 场景：发布了新视频"忽然"，想推广给所有评论用户

# 1. 准备信息
源视频BV号: BV1TRzZBuEg6
推广视频链接: https://www.bilibili.com/video/BV1EYf4BQE7q
视频标题: 忽然

# 2. 运行脚本
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"

# 3. 观察输出
# [爬虫] 完整获取所有评论用户
# [完成] 共获取 61 位用户
# [发送] 开始批量发送...
# [完成] 成功: 20, 跳过: 0, 失败: 2
```

### 断点续传

```bash
# 场景：发送到第20条时停止了，想继续发送

# 直接再次运行（保持参数一致）
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --keep-users

# 脚本会显示：
# [记录] 已发送记录: 20 位用户
# [过滤] 待发送: 41 位，已跳过: 20 位
```

---

## 注意事项

1. ✅ **发送记录永久保留**：即使删除用户数据，发送记录也会保留
2. ✅ **默认跳过已发送**：避免重复发送给同一用户
3. ✅ **支持中断续传**：随时可以停止，下次继续
4. ✅ **批量自动发送**：每批10位用户，批内0-10秒延迟，批间100-200秒延迟
5. ⚠️ **首次使用**：建议先用 `--dry-run` 测试

### 批量发送时间估算

**示例：61位用户**
- 总批次数：7批（前6批各10人，最后1批1人）
- 预计时间：
  - 批内发送时间：约 50秒（61 × 平均5秒）
  - 批次间隔时间：约 18分钟（6个间隔 × 平均180秒）
  - **总计：约 19-20分钟**

**示例：100位用户**
- 总批次数：10批
- 预计时间：
  - 批内发送时间：约 8分钟（100 × 平均5秒）
  - 批次间隔时间：约 30分钟（9个间隔 × 平均200秒）
  - **总计：约 38-40分钟**
