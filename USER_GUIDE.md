# 给用户的使用说明

## 如何运行推广

当你需要推广新视频时，只需要提供3个参数：

### 必需参数

1. **源视频BV号** - 从哪个视频抓取评论用户
2. **推广视频链接** - 推广哪个视频  
3. **视频标题** - 推广视频的标题

---

## 使用方法

### 命令行直接运行（推荐）

 python run_campaign.py BV138ByY1ET1  --video-url "https://www.bilibili.com/video/BV19kf4ByE6E/?spm_id_from=333.337.search-card.all.click&vd_source=c2469c7e24b87453c21342a5f8de7b84" --title "墙上的向日葵" 

```bash
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"
```

**参数说明：**
- `BV1TRzZBuEg6` → 源视频BV号（从这个视频抓取评论用户）
- `--video-url` → 你要推广的视频链接
- `--title` → 推广视频的标题

---

## 实际使用示例

### 推广新视频

```bash
# 推广视频"忽然"给BV1TRzZBuEg6的所有评论用户
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然"
```

**程序会自动执行：**
1. 删除旧用户数据（保留发送记录）
2. 从 BV1TRzZBuEg6 抓取评论用户
3. 发送私信（自动跳过已发送的）
4. 保存发送记录

### 继续发送（中断后）

```bash
# 发送到一半停止了？加 --keep-users 再运行
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --keep-users
```

### 试运行（测试）

```bash
# 加上 --dry-run 参数，不会实际发送
python run_campaign.py BV1TRzZBuEg6 \
  --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" \
  --title "忽然" \
  --dry-run
```

---

## 常用命令

| 需求 | 命令 |
|------|------|
| 完整流程 | `python run_campaign.py BV号 --video-url "链接" --title "标题"` |
| 只抓取用户 | `python run_campaign.py BV号 --video-url "链接" --title "标题" --fetch-only` |
| 试运行 | `python run_campaign.py BV号 --video-url "链接" --title "标题" --dry-run` |
| 保留用户数据 | `python run_campaign.py BV号 --video-url "链接" --title "标题" --keep-users` |

---

## 流程说明

### 自动流程

```
开始 → 删除旧用户数据 → 抓取评论用户 → 过滤已发送 → 批量发送 → 完成
       (保留发送记录)     (主评论+子回复)   (读取记录)   (保存记录)
```

### 数据管理

**删除的文件：**
- `data/users/*.json` - 用户数据文件（可重新抓取）

**保留的文件：**
- `data/sent_records/*.json` - 发送记录文件（永久保留，避免重复）

---

## 参数获取

### 如何获取BV号

1. 打开B站视频页面
2. 复制URL中的BV号
   - 例如：`https://www.bilibili.com/video/BV1TRzZBuEg6`
   - BV号就是：`BV1TRzZBuEg6`

### 如何获取视频链接

完整复制视频URL即可：
- `https://www.bilibili.com/video/BV1EYf4BQE7q`

### 视频标题

填写视频的标题，用于私信消息模板：
- 例如：`忽然`、`新视频发布`、`最新作品` 等
