# B站私信推广 - 配置文件
# 使用方法：复制此文件为 config.local.py 并填写参数

# ========== 推广配置 ==========
# 源视频BV号（抓取这个视频的评论用户）
SOURCE_BV_ID = "BV1TRzZBuEg6"

# 推广的视频链接
PROMOTE_VIDEO_URL = "https://www.bilibili.com/video/BV1EYf4BQE7q"

# 推广的视频标题
PROMOTE_VIDEO_TITLE = "忽然"

# ========== 高级配置 ==========
# 最多抓取用户数
MAX_USERS = 1000

# 是否跳过已发送用户（默认True）
SKIP_SENT = True

# 是否只抓取用户（不发送）
FETCH_ONLY = False

# 是否保留旧用户数据
KEEP_USERS = False
