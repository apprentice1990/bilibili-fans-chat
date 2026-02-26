#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量测试脚本：向多个用户发送私信
使用新的直接导航方法
"""

import json
import pickle
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def load_users_from_json(json_file):
    """从JSON文件加载用户列表"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['users']

def send_to_user(driver, user_id, nickname, message):
    """向用户发送私信"""
    try:
        # 直接导航到私信页面
        msg_url = f"https://message.bilibili.com/#/whisper/mid{user_id}"
        driver.get(msg_url)
        time.sleep(random.uniform(3, 5))

        # 使用JavaScript填写消息并发送
        result = driver.execute_script("""
            var message = arguments[0];

            // 1. 填写消息到textarea
            var textareas = document.querySelectorAll('textarea');
            if (textareas.length === 0) {
                return {success: false, error: '未找到输入框'};
            }

            var textarea = textareas[textareas.length - 1];
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
            return {"status": "failed", "reason": result.get('error', '未知错误')}

    except Exception as e:
        return {"status": "failed", "reason": str(e)[:200]}

def main():
    print("\n" + "="*60)
    print("批量发送测试（用户4-7，使用新方法）")
    print("="*60)

    # 加载用户列表
    json_file = "data/users/BV1TRzZBuEg6_20260225_163222.json"

    if not Path(json_file).exists():
        print(f"[错误] 文件不存在: {json_file}")
        return

    users = load_users_from_json(json_file)
    print(f"[OK] 已加载 {len(users)} 位用户")

    # 准备消息
    bv_id = "BV1TRzZBuEg6"
    video_url = f"https://www.bilibili.com/video/{bv_id}"
    title = "忽然"

    # 加载模板
    template_file = "templates/message_template.txt"
    if Path(template_file).exists():
        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()
    else:
        template = msg_config.DEFAULT_MESSAGE_TEMPLATE

    message = template.format(title=title, video_url=video_url)

    print(f"\n消息内容:")
    print("-"*60)
    print(message)
    print("-"*60)

    # 测试用户4-7
    start_index = 3  # 用户4
    end_index = 7     # 到用户7

    print(f"\n测试用户（用户{start_index+1}-{end_index}）:")
    for i in range(start_index, end_index):
        user = users[i]
        print(f"  {i+1}. {user['nickname']} (ID: {user['user_id']}, 赞: {user['like_count']})")

    # 确认
    print(f"\n[提示] 将依次测试用户{start_index+1}-{end_index}")
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("[自动] 自动确认模式")
    else:
        confirm = input("\n确认开始？(yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("[取消] 已取消")
            return

    # 初始化浏览器
    print("\n[浏览器] 初始化中...")
    options = Options()
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        # 加载cookies
        print("\n[Cookies] 加载中...")
        cookie_path = msg_config.COOKIE_FILE

        if not cookie_path.exists():
            print(f"[错误] Cookies不存在: {cookie_path}")
            return

        driver.get("https://www.bilibili.com")
        time.sleep(2)

        with open(cookie_path, 'rb') as f:
            cookies = pickle.load(f)

        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                continue

        print(f"[OK] 已加载 {len(cookies)} 个cookies")
        driver.refresh()
        time.sleep(2)

        # 批量发送
        stats = {"success": 0, "skip": 0, "failed": 0}

        for i in range(start_index, end_index):
            user = users[i]
            print(f"\n{'='*60}")
            print(f"发送给 {i+1}/{len(users)}: {user['nickname']}")
            print(f"{'='*60}")

            result = send_to_user(driver, user['user_id'], user['nickname'], message)

            if result['status'] == 'success':
                stats['success'] += 1
                print(f"  [OK] 发送成功！")
                # 发送成功就停止测试
                break
            else:
                stats['failed'] += 1
                print(f"  [FAIL] 失败: {result['reason']}")

            # 用户间延迟
            if i < end_index - 1:
                print(f"\n[等待] 10秒后继续下一位用户...")
                time.sleep(10)

        # 显示统计
        print(f"\n{'='*60}")
        print("测试完成")
        print(f"{'='*60}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failed']}")

        if stats['success'] > 0:
            print(f"\n[OK] 测试成功！已成功发送私信")
        else:
            print(f"\n[提示] 所有用户都发送失败")

        # 等待查看结果
        print("\n[提示] 浏览器将保持打开30秒，请查看结果...")
        time.sleep(30)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
