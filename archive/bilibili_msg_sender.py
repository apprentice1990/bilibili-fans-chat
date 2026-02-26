#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站私信推广工具 - 主程序
功能：向视频评论用户发送私信推广新视频
"""

import os
import sys
import time
import random
import pickle
import json
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import msg_config
from msg_config import (
    COOKIE_FILE,
    MESSAGE_TEMPLATE_FILE,
    DEFAULT_MESSAGE_TEMPLATE,
    MAX_MESSAGE_LENGTH,
    CONFIRM_BEFORE_SEND,
    SHOW_PROGRESS,
    PROGRESS_UPDATE_INTERVAL,
    PAGE_LOAD_TIMEOUT,
    ELEMENT_WAIT_TIMEOUT,
    BILIBILI_HOME,
    USER_SPACE_URL,
    MESSAGE_BUTTON_XPATH,
    MESSAGE_INPUT_SELECTOR,
    SEND_BUTTON_XPATH,
    RECORDS_DIR
)
from rate_limiter import RateLimiter
from comment_fetcher import CommentFetcher


class BilibiliMessageSender:
    """B站私信发送器"""

    def __init__(self):
        """初始化发送器"""
        self.driver = None
        self.wait = None
        self.rate_limiter = RateLimiter()
        self.stats = {
            "success": 0,
            "skip": 0,
            "failed": 0
        }

    def init_browser(self):
        """初始化浏览器"""
        print("\n[浏览器] 正在初始化...")

        options = Options()

        # 基本配置
        window_size = msg_config.CHROME_OPTIONS.get('window_size', '1400,900')
        options.add_argument(f'--window-size={window_size}')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # 反检测配置
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 创建WebDriver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        self.wait = WebDriverWait(self.driver, ELEMENT_WAIT_TIMEOUT)

        print("[OK] 浏览器初始化完成")

    def load_cookies(self):
        """加载cookies"""
        print(f"\n[Cookies] 正在加载: {COOKIE_FILE}")

        if not COOKIE_FILE.exists():
            print(f"[错误] Cookies文件不存在: {COOKIE_FILE}")
            print("[提示] 请先使用bilibili_video_pipeline登录B站获取cookies")
            return False

        try:
            # 先访问B站首页
            self.driver.get(BILIBILI_HOME)
            time.sleep(2)

            # 加载cookies
            with open(COOKIE_FILE, 'rb') as f:
                cookies = pickle.load(f)

            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    continue

            print(f"[OK] 已加载 {len(cookies)} 个cookies")

            # 刷新页面验证登录
            self.driver.refresh()
            time.sleep(2)

            return True

        except Exception as e:
            print(f"[错误] Cookies加载失败: {e}")
            return False

    def send_to_user(self, user_id, message):
        """
        向用户发送私信（使用直接导航到私信页面的方法）

        参数:
            user_id: 用户ID
            message: 消息内容

        返回:
            dict: 发送结果
        """
        try:
            # 直接导航到私信页面
            msg_url = f"https://message.bilibili.com/#/whisper/mid{user_id}"
            self.driver.get(msg_url)
            time.sleep(random.uniform(3, 5))

            # 使用JavaScript填写消息并发送
            result = self.driver.execute_script("""
                var message = arguments[0];

                // 1. 填写消息到textarea
                var textareas = document.querySelectorAll('textarea');
                if (textareas.length === 0) {
                    return {success: false, error: '未找到输入框', step: 'find-textarea'};
                }

                var textarea = textareas[textareas.length - 1]; // 使用最后一个
                textarea.value = message;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.dispatchEvent(new Event('change', { bubbles: true }));

                // 2. 使用Ctrl+Enter发送
                var event = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    which: 13,
                    keyCode: 13,
                    bubbles: true,
                    ctrlKey: true
                });
                textarea.dispatchEvent(event);

                return {success: true, method: 'Ctrl+Enter'};
            """, message)

            if result.get('success'):
                time.sleep(2)
                return {"status": "success"}
            else:
                error = result.get('error', '未知错误')
                step = result.get('step', 'unknown')
                return {"status": "failed", "reason": f"{error} (步骤: {step})"}

        except Exception as e:
            return {"status": "failed", "reason": str(e)}

    def record_send(self, user_id, nickname, status, reason=""):
        """
        记录发送结果

        参数:
            user_id: 用户ID
            nickname: 用户昵称
            status: 状态 (success/skip/failed)
            reason: 原因
        """
        date = datetime.now().strftime("%Y%m%d")
        record_file = RECORDS_DIR / f"sent_{date}.json"

        record = {
            "user_id": user_id,
            "nickname": nickname,
            "status": status,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        # 加载现有记录
        if record_file.exists():
            with open(record_file, 'r', encoding='utf-8') as f:
                try:
                    records = json.load(f)
                except:
                    records = []
        else:
            records = []

        # 追加新记录
        records.append(record)

        # 保存
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def load_message_template(self):
        """
        加载消息模板

        返回:
            str: 消息模板内容
        """
        if MESSAGE_TEMPLATE_FILE.exists():
            with open(MESSAGE_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"[警告] 模板文件不存在，使用默认模板: {MESSAGE_TEMPLATE_FILE}")
            return DEFAULT_MESSAGE_TEMPLATE

    def format_message(self, template, title, video_url):
        """
        格式化消息

        参数:
            template: 消息模板
            title: 视频标题
            video_url: 视频链接

        返回:
            str: 格式化后的消息
        """
        message = template.format(title=title, video_url=video_url)

        # 检查长度
        if len(message) > MAX_MESSAGE_LENGTH:
            print(f"[警告] 消息长度 {len(message)} 超过限制 {MAX_MESSAGE_LENGTH}，将截断")
            message = message[:MAX_MESSAGE_LENGTH]

        return message

    def confirm_before_send(self, users, message, bv_id):
        """
        发送前确认

        参数:
            users: 用户列表
            message: 消息内容
            bv_id: 视频BV号

        返回:
            bool: 是否确认发送
        """
        print("\n" + "="*60)
        print("发送确认")
        print("="*60)
        print(f"视频BV号: {bv_id}")
        print(f"目标用户数: {len(users)}")
        print(f"\n消息内容:")
        print("-"*60)
        print(message)
        print("-"*60)

        # 预览前3位用户
        print(f"\n目标用户预览 (前3位):")
        for i, user in enumerate(users[:3], 1):
            print(f"  {i}. {user['nickname']} (ID: {user['user_id']})")

        if len(users) > 3:
            print(f"  ... 还有 {len(users)-3} 位用户")

        # 预计耗时
        total_seconds = len(users) * random.randint(30, 90)
        total_minutes = total_seconds // 60
        print(f"\n预计耗时: 约 {total_minutes} 分钟")

        print("="*60)

        # 确认
        if CONFIRM_BEFORE_SEND:
            while True:
                response = input("\n确认发送? (yes/no): ").strip().lower()
                if response in ['yes', 'y', '是']:
                    return True
                elif response in ['no', 'n', '否']:
                    return False
                else:
                    print("请输入 yes 或 no")
        else:
            return True

    def batch_send(self, users, message):
        """
        批量发送私信

        参数:
            users: 用户列表
            message: 消息内容
        """
        print("\n" + "="*60)
        print("开始批量发送")
        print("="*60)

        total = len(users)

        for i, user in enumerate(users, 1):
            # 显示进度
            if SHOW_PROGRESS and i % PROGRESS_UPDATE_INTERVAL == 0:
                print(f"\n[{i}/{total}] 进度: {i*100//total}%")

            print(f"\n[{i}/{total}] 发送给 {user['nickname']}...")

            # 速率限制
            self.rate_limiter.wait_if_needed()

            # 发送
            result = self.send_to_user(user['user_id'], message)

            # 记录
            self.record_send(
                user['user_id'],
                user['nickname'],
                result['status'],
                result.get('reason', '')
            )

            # 更新统计
            if result['status'] == 'success':
                self.stats['success'] += 1
                print(f"  ✓ 成功")
            elif result['status'] == 'skip':
                self.stats['skip'] += 1
                print(f"  → 跳过：{result['reason']}")
            else:
                self.stats['failed'] += 1
                print(f"  ✗ 失败：{result['reason']}")

        # 显示统计
        self.show_summary()

    def show_summary(self):
        """显示统计摘要"""
        print("\n" + "="*60)
        print("发送完成统计")
        print("="*60)
        print(f"总计: {self.stats['success'] + self.stats['skip'] + self.stats['failed']}")
        print(f"成功: {self.stats['success']} ✓")
        print(f"跳过: {self.stats['skip']} →")
        print(f"失败: {self.stats['failed']} ✗")
        print("="*60)

        # 速率统计
        rate_stats = self.rate_limiter.get_stats()
        print(f"\n速率统计:")
        print(f"运行时间: {rate_stats['elapsed_minutes']} 分钟")
        print(f"平均速率: {rate_stats['avg_rate_per_hour']:.2f} 条/小时")

    def run(self, bv_id, video_title=None, custom_message=None):
        """
        运行发送流程

        参数:
            bv_id: 视频BV号
            video_title: 视频标题（可选）
            custom_message: 自定义消息（可选）
        """
        print("\n" + "#"*60)
        print("# B站私信推广工具")
        print("#"*60)
        print(f"视频BV号: {bv_id}")
        print(f"视频标题: {video_title or '未指定'}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*60)

        # 1. 初始化浏览器
        self.init_browser()

        # 2. 加载cookies
        if not self.load_cookies():
            print("\n[错误] Cookies加载失败，无法继续")
            return False

        # 3. 获取评论用户
        print(f"\n[步骤1] 获取评论用户")
        fetcher = CommentFetcher(self.driver)
        users = fetcher.fetch_comments(bv_id)

        if not users:
            print("\n[错误] 未获取到任何用户")
            return False

        # 4. 准备消息
        print(f"\n[步骤2] 准备消息")

        if custom_message:
            message = custom_message
        else:
            template = self.load_message_template()
            video_url = f"https://www.bilibili.com/video/{bv_id}"
            message = self.format_message(template, video_title or "新视频", video_url)

        # 5. 确认发送
        if not self.confirm_before_send(users, message, bv_id):
            print("\n[取消] 已取消发送")
            return False

        # 6. 批量发送
        print(f"\n[步骤3] 开始批量发送")
        self.batch_send(users, message)

        # 7. 完成
        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n所有记录已保存到: data/records/")

        return True

    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("\n[浏览器] 已关闭")


def main():
    """主函数"""
    import argparse
    import msg_config

    parser = argparse.ArgumentParser(description='B站私信推广工具')
    parser.add_argument('bv_id', nargs='?', help='视频BV号')
    parser.add_argument('--title', '-t', help='视频标题')
    parser.add_argument('--message', '-m', help='自定义消息内容')

    args = parser.parse_args()

    # 获取BV号
    if args.bv_id:
        bv_id = args.bv_id
    else:
        bv_id = input("请输入视频BV号: ").strip()

    # 验证BV号格式
    if not bv_id.startswith('BV'):
        print("[错误] BV号格式错误，应以'BV'开头")
        return 1

    # 创建发送器
    sender = BilibiliMessageSender()

    try:
        # 运行
        success = sender.run(
            bv_id=bv_id,
            video_title=args.title,
            custom_message=args.message
        )

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n[中断] 用户手动中断")
        return 1

    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        sender.close()


if __name__ == "__main__":
    sys.exit(main())
