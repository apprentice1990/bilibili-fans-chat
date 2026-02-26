# MediaCrawler集成完成指南

## 🎉 集成成功!

MediaCrawler已成功集成到你的B站私信推广项目中!

## 📊 测试结果

### BV1hf4y1L763 (60万播放)
- **原API方案**: 131位用户
- **MediaCrawler**: 463位用户
- **提升**: +253.4% ⬆️

## 📁 项目结构

```
bilibili_fans_chat/
├── MediaCrawler/                    # MediaCrawler爬虫工具
│   ├── config/                      # 配置文件
│   │   ├── base_config.py          # 基础配置
│   │   └── bilibili_config.py      # B站配置
│   ├── data/bili/json/              # 爬取的数据
│   └── main.py                      # 运行入口
├── data/users/                      # 转换后的用户数据
│   └── BV1hf4y1L763_mediacrawler_*.json
├── convert_media_crawler_data.py    # 数据转换工具
├── compare_results.py               # 对比分析工具
└── MEDIACRAWLER_REPORT.md           # 详细测试报告
```

## 🚀 快速开始

### 方式1: 使用MediaCrawler爬取(推荐)

#### 步骤1: 配置视频BV号

编辑 `MediaCrawler/config/bilibili_config.py`:

```python
BILI_SPECIFIED_ID_LIST = [
    "BV1hf4y1L763",  # 添加你的视频BV号
    # 可以添加多个BV号
    "BV1xxxxxxxxxx",
]
```

#### 步骤2: 调整爬取参数(可选)

编辑 `MediaCrawler/config/base_config.py`:

```python
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 1000  # 每个视频最多爬取评论数
ENABLE_GET_SUB_COMMENTS = True  # 启用二级评论
```

#### 步骤3: 运行爬虫

```bash
cd MediaCrawler
python main.py --platform bili --lt qrcode --type detail
```

首次运行需要扫码登录:
1. 程序会打开浏览器
2. 显示二维码
3. 用B站手机App扫码登录
4. 等待登录完成

#### 步骤4: 转换数据

爬取完成后,转换数据为标准格式:

```bash
cd ..
python convert_media_crawler_data.py
```

默认会转换最新的数据文件,输出到 `data/users/` 目录。

### 方式2: 使用原API方案(快速测试)

```bash
python fetch_all_replies_complete.py BV1hf4y1L763 1000
```

数据保存到 `data/users/BV1hf4y1L763_complete_*.json`

## 📈 对比两种方案

| 特性 | MediaCrawler | 原API方案 |
|------|-------------|-----------|
| 用户数量(60万播放视频) | 463位 | 131位 |
| 提升率 | 基准 | -253.4% |
| 技术方案 | 浏览器自动化 | API请求 |
| 安装难度 | 中等(需安装浏览器) | 简单 |
| 运行速度 | 较慢 | 快 |
| 数据完整性 | 高 | 低(受API限制) |
| 长期维护 | ✅ 活跃(43k+ stars) | ⚠️ 自主维护 |

**推荐**: 对于高播放量视频(>10万),强烈推荐使用MediaCrawler。

## 🎯 使用场景建议

### 使用MediaCrawler:
✅ 高播放量视频(>10万播放)
✅ 需要大量用户数据
✅ 长期使用的项目
✅ 需要数据完整性

### 使用原API方案:
✅ 快速测试
✅ 低播放量视频(<1万播放)
✅ 不想安装浏览器
✅ 只需要少量用户

## 🔧 高级用法

### 批量爬取多个视频

编辑 `MediaCrawler/config/bilibili_config.py`:

```python
BILI_SPECIFIED_ID_LIST = [
    "BV1hf4y1L763",
    "BV1xxxxxxxx1",
    "BV1xxxxxxxx2",
    "BV1xxxxxxxx3",
]
```

然后运行 `python main.py --platform bili --lt qrcode --type detail`

### 定时爬取

使用Windows任务计划程序或cron定时运行:

```bash
# 每天凌晨2点运行
0 2 * * * cd /path/to/bilibili_fans_chat/MediaCrawler && python main.py --platform bili --lt cookie --type detail
```

### 数据去重

跨多次运行去重用户:

```bash
python convert_media_crawler_data.py --input MediaCrawler/data/bili/json/detail_comments_2026-02-26.json
```

转换脚本会自动去重用户ID。

## 📝 数据格式

两种方案输出的数据格式完全一致:

```json
{
  "bv_id": "BV1hf4y1L763",
  "fetched_at": "2026-02-26T16:57:51.226287",
  "total_users": 463,
  "users": [
    {
      "user_id": "12624122",
      "nickname": "_念言温玉",
      "comment": "热河省都没了[大哭]"
    }
  ]
}
```

## ⚠️ 注意事项

1. **首次登录**: MediaCrawler首次使用需要扫码登录,之后会缓存登录状态
2. **爬取间隔**: 建议每次爬取间隔1-2小时,避免被B站限制
3. **数据存储**: MediaCrawler的数据保存在 `MediaCrawler/data/bili/json/` 目录
4. **浏览器驱动**: Chromium约135MB,首次下载需要时间
5. **二维码登录**: 有效期约20秒,超时需重新运行

## 🎊 测试成功数据

```
视频: BV1hf4y1L763 (你离开了南京,从此没有人和我说话)
播放量: 60万

原API方案:
- 唯一用户: 131位

MediaCrawler方案:
- 总评论: 540条
- 唯一用户: 463位
- 提升: +253.4%
```

## 📚 相关文档

- `MEDIACRAWLER_REPORT.md` - 详细测试报告
- `README.md` - 项目总体说明
- `USER_GUIDE.md` - 用户使用指南

## 🤝 获取帮助

如遇问题:
1. 查看详细报告: `MEDIACRAWLER_REPORT.md`
2. 对比数据: `python compare_results.py`
3. 查看日志: 运行时的控制台输出

---

**恭喜!你现在可以使用MediaCrawler获取3倍以上的B站评论用户了!** 🎉
