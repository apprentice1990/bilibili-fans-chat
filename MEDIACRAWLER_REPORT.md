# MediaCrawler集成测试报告

## 测试视频
- **BV号**: BV1hf4y1L763
- **标题**: 你离开了南京,从此没有人和我说话
- **播放量**: 60万

## 测试结果对比

### 方案1: MediaCrawler (浏览器自动化)
- **总评论数**: 540条
- **唯一用户数**: 463位
- **技术方案**: Playwright浏览器自动化
- **登录方式**: 二维码登录
- **评论类型**: 一级评论 + 二级评论

### 方案2: 原API方案 (fetch_all_replies_complete.py)
- **唯一用户数**: 131位
- **技术方案**: B站API + requests库
- **认证方式**: Cookies (bilibili_cookies.pkl)
- **评论类型**: 一级评论 + 二级评论
- **限制**: B站API只返回最新19条主评论

## 效果提升

```
用户数: 131 → 463
增加: +332位用户
提升率: +253.4%
```

## 关键发现

### 1. MediaCrawler的优势
✅ **突破API限制**: 使用浏览器自动化,绕过了B站API的19条主评论限制
✅ **更多数据**: 获取了463位用户,比原方案多253.4%
✅ **真实用户环境**: 使用已登录的Chrome浏览器,模拟真实用户行为
✅ **二级评论**: 完整支持二级评论爬取
✅ **CDP模式**: 支持Chrome DevTools Protocol,反检测能力更强

### 2. 原API方案的局限
❌ **API限制**: B站API只返回最新19条主评论,无法获取历史评论
❌ **重复数据**: 分页请求返回相同的主评论,无法突破
❌ **数据有限**: 即使获取二级评论,总用户数仍受限于主评论数量

### 3. 数据对比
| 指标 | MediaCrawler | 原API方案 | 提升 |
|------|-------------|-----------|------|
| 唯一用户数 | 463 | 131 | +253.4% |
| 总评论数 | 540 | 未知 | - |
| 数据完整性 | 高 | 低 | - |

## 使用建议

### 推荐方案: MediaCrawler

**优点**:
1. 获取用户数量提升2.5倍以上
2. 数据更全面、更准确
3. 活跃维护,社区支持好(43k+ stars)
4. 支持多平台(小红书、抖音、快手、B站等)
5. 有WebUI可视化界面

**缺点**:
1. 需要安装浏览器驱动(Chromium ~135MB)
2. 首次登录需要扫码
3. 相对较慢(需要启动浏览器)

### 适用场景

**使用MediaCrawler**:
- 需要获取大量用户(>200)
- 高播放量视频(>10万播放)
- 需要全面数据
- 长期使用的项目

**使用原API方案**:
- 快速测试
- 低播放量视频(<1万播放)
- 不想安装浏览器驱动
- 只需要少量用户

## MediaCrawler集成步骤

### 1. 安装
```bash
cd MediaCrawler
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. 配置
编辑 `config/base_config.py`:
```python
PLATFORM = "bili"  # 平台
CRAWLER_TYPE = "detail"  # 爬取类型
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 1000  # 每个视频最多评论数
ENABLE_GET_SUB_COMMENTS = True  # 启用二级评论
```

编辑 `config/bilibili_config.py`:
```python
BILI_SPECIFIED_ID_LIST = [
    "BV1hf4y1L763",  # 添加你的视频BV号
]
```

### 3. 运行
```bash
python main.py --platform bili --lt qrcode --type detail
```

### 4. 数据位置
爬取的数据保存在:
```
MediaCrawler/data/bili/json/detail_comments_YYYY-MM-DD.json
```

## 结论

**MediaCrawler在获取B站评论用户方面明显优于原API方案**

对于BV1hf4y1L763这个60万播放的视频:
- 原API方案只能获取131位用户
- MediaCrawler可以获取463位用户
- **提升率达253.4%**

**建议**: 对于私信推广项目,使用MediaCrawler可以获取更多潜在用户,提高推广效果。

## 下一步建议

1. **批量处理**: 修改BILI_SPECIFIED_ID_LIST,添加多个视频BV号
2. **数据整合**: 将MediaCrawler的JSON数据转换为现有格式,集成到私信发送流程
3. **定时任务**: 设置定时运行,定期获取新评论用户
4. **数据去重**: 跨多次运行进行用户去重,避免重复发送
5. **WebUI使用**: 使用MediaCrawler的WebUI界面进行可视化操作

---
*测试时间: 2026-02-26*
*测试环境: Windows 11, Python 3.11.9*
*MediaCrawler版本: latest (2026-02-26)*
