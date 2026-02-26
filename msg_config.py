#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站私信推广配置文件
"""

import os
from pathlib import Path

# ==================== 项目路径配置 ====================
# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# Cookies文件路径（复用bilibili_video_pipeline的cookies）
COOKIE_FILE = PROJECT_ROOT.parent / "bilibili_video_pipeline" / "bilibili_cookies.pkl"

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
USERS_DIR = DATA_DIR / "users"
RECORDS_DIR = DATA_DIR / "records"

# 模板目录
TEMPLATES_DIR = PROJECT_ROOT / "templates"
MESSAGE_TEMPLATE_FILE = TEMPLATES_DIR / "message_template.txt"

# ==================== 发送配置 ====================
# 每日最大发送量（保守策略）
MAX_DAILY_SENDS = 50

# 每个视频最多获取用户数
MAX_USERS_PER_VIDEO = 100

# 发送间隔（秒）
MIN_INTERVAL = 30  # 最小间隔30秒
MAX_INTERVAL = 90  # 最大间隔90秒

# 批次暂停配置
BATCH_SIZE = 10        # 每发送10条后暂停
BATCH_PAUSE = 300      # 暂停5分钟（300秒）

# 每小时最大发送量
MAX_SENDS_PER_HOUR = 20

# ==================== 浏览器配置 ====================
# 窗口大小
WINDOW_SIZE = "1400,900"

# Chrome选项
CHROME_OPTIONS = {
    'disable_gpu': True,
    'no_sandbox': True,
    'disable_dev_shm_usage': True,
    'disable_automation_extension': True,
    'exclude_switches': ['enable-logging'],
}

# 页面加载超时（秒）
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 10

# ==================== 用户筛选配置 ====================
# 最低点赞数（0=不限制）
MIN_LIKES = 0

# 是否排除官方账号
EXCLUDE_OFFICIAL = True

# 官方账号列表（昵称包含这些关键词的用户将被排除）
OFFICIAL_KEYWORDS = [
    "BILIBILI",
    "哔哩哔哩",
    "官方",
    "管理员",
]

# ==================== 消息配置 ====================
# 默认消息模板
DEFAULT_MESSAGE_TEMPLATE = """你好！看到你在我的视频下评论，感谢支持！

最近发布了一个新视频《{title}》，
希望能给你带来不一样的体验：

{video_url}

如果打扰请见谅～"""

# 消息最大长度（B站私信限制）
MAX_MESSAGE_LENGTH = 2000

# ==================== 日志配置 ====================
# 是否显示详细日志
VERBOSE = True

# 日志级别: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_LEVEL = 'INFO'

# ==================== 重试配置 ====================
# 最大重试次数
MAX_RETRIES = 2

# 重试延迟（秒）
RETRY_DELAYS = [60, 300]  # 1分钟，5分钟

# ==================== 安全配置 ====================
# 是否在发送前确认
CONFIRM_BEFORE_SEND = True

# 是否显示实时进度
SHOW_PROGRESS = True

# 每发送N条显示一次进度
PROGRESS_UPDATE_INTERVAL = 1

# ==================== B站URL配置 ====================
# 用户主页URL格式
USER_SPACE_URL = "https://space.bilibili.com/{}"

# 视频页面URL格式
VIDEO_URL = "https://www.bilibili.com/video/{}"

# B站首页
BILIBILI_HOME = "https://www.bilibili.com"

# ==================== CSS选择器配置 ====================
# 评论相关选择器（提供多个备选）
COMMENT_ITEM_SELECTORS = [
    ".reply-item",           # 主要选择器
    ".reply-item ",          # 备用1
    "[class*='reply-item']", # 备用2（包含reply-item的类）
]
COMMENT_ITEM_SELECTOR = ".reply-item"

USER_INFO_SELECTOR = ".user-info a"
USER_INFO_SELECTORS = [
    ".user-info a",          # 主要选择器
    ".sub-user-name a",      # 备用1
    "[class*='user-name'] a", # 备用2
]

USER_ID_ATTR = "data-user-id"
COMMENT_CONTENT_SELECTOR = ".reply-content"
COMMENT_CONTENT_SELECTORS = [
    ".reply-content",
    ".reply-text",
    "[class*='reply-text']",
]

# 私信相关选择器
MESSAGE_BUTTON_XPATH = "//a[contains(text(), '发消息')]"
MESSAGE_INPUT_SELECTOR = "textarea"
SEND_BUTTON_XPATH = "//button[contains(text(), '发送')]"
CLOSE_BUTTON_XPATH = "//button[@class='close']"

# ==================== 确保目录存在 ====================
def ensure_directories():
    """确保所有必要的目录存在"""
    directories = [
        DATA_DIR,
        USERS_DIR,
        RECORDS_DIR,
        TEMPLATES_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# 自动创建目录
ensure_directories()
