#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：逐个测试用户，截图保存问题
"""

import json
import pickle
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def load_users_from_json(json_file):
    """从JSON文件加载用户列表"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['users']

def debug_user(driver, wait, user_id, nickname, screenshot_dir):
    """调试单个用户"""
    url = f"https://space.bilibili.com/{user_id}"

    try:
        print(f"  [访问] {url}")
        driver.get(url)

        # 等待页面加载
        time.sleep(5)

        # 截图
        screenshot_path = screenshot_dir / f"user_{user_id}_01_page.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"  [截图] {screenshot_path.name}")

        # 查找"发消息"按钮
        try:
            msg_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '发消息')]"))
            )
            print(f"  [OK] 找到发消息按钮")

            # 截图按钮位置
            screenshot_path2 = screenshot_dir / f"user_{user_id}_02_button.png"
            driver.save_screenshot(str(screenshot_path2))
            print(f"  [截图] {screenshot_path2.name}")

            return {"status": "can_send"}

        except Exception as e:
            print(f"  [SKIP] 未找到发消息按钮: {str(e)[:100]}")

            # 截图当前状态
            screenshot_path3 = screenshot_dir / f"user_{user_id}_03_no_button.png"
            driver.save_screenshot(str(screenshot_path3))
            print(f"  [截图] {screenshot_path3.name}")

            return {"status": "skip", "reason": "未找到发消息按钮"}

    except Exception as e:
        print(f"  [FAIL] 错误: {str(e)[:200]}")
        return {"status": "failed", "reason": str(e)[:200]}

def main():
    print("\n" + "="*60)
    print("调试模式：逐个测试用户（带截图）")
    print("="*60)

    # 加载用户列表
    json_file = "data/users/BV1TRzZBuEg6_20260225_163222.json"

    if not Path(json_file).exists():
        print(f"[错误] 文件不存在: {json_file}")
        return

    users = load_users_from_json(json_file)
    print(f"[OK] 已加载 {len(users)} 位用户")

    # 创建截图目录
    screenshot_dir = Path("debug_screenshots")
    screenshot_dir.mkdir(exist_ok=True)
    print(f"[截图] 保存目录: {screenshot_dir}")

    # 测试第4-10位用户
    start_index = 3
    end_index = min(10, len(users))

    print(f"\n[测试] 用户 {start_index+1}-{end_index}:")

    for i in range(start_index, end_index):
        user = users[i]
        print(f"\n{i+1}. {user['nickname']} (ID: {user['user_id']})")

    # 确认
    print(f"\n[提示] 将测试用户{start_index+1}-{end_index}，并保存截图")
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
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--hide-scrollbars')
    options.add_argument('--metrics-recording-only')
    options.add_argument('--mute-audio')
    options.add_argument('--no-first-run')
    options.add_argument('--safebrowsing-disable-auto-update')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--log-level=3')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    wait = WebDriverWait(driver, 10)

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

        # 测试用户
        stats = {"can_send": 0, "skip": 0, "failed": 0}

        for i in range(start_index, end_index):
            user = users[i]
            print(f"\n{'='*60}")
            print(f"测试用户 {i+1}/{len(users)}: {user['nickname']}")
            print(f"{'='*60}")

            result = debug_user(driver, wait, user['user_id'], user['nickname'], screenshot_dir)

            if result['status'] == 'can_send':
                stats['can_send'] += 1
                print(f"  [OK] 可以发送私信！")
            elif result['status'] == 'skip':
                stats['skip'] += 1
                print(f"  [SKIP] 跳过")
            else:
                stats['failed'] += 1
                print(f"  [FAIL] 失败")

            # 用户间延迟
            if i < end_index - 1:
                print(f"\n[等待] 3秒后继续...")
                time.sleep(3)

        # 显示统计
        print(f"\n{'='*60}")
        print("调试完成")
        print(f"{'='*60}")
        print(f"可发送: {stats['can_send']}")
        print(f"跳过: {stats['skip']}")
        print(f"失败: {stats['failed']}")

        print(f"\n[截图] 已保存到: {screenshot_dir}")

        # 等待查看结果
        print("\n[提示] 浏览器将保持打开60秒，请查看结果...")
        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
