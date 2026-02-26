#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：向第4-6位用户发送私信（跳过前3位）
直到找到可以发送的用户或测试完3个用户
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

def send_message_to_user(driver, wait, user_id, nickname, message):
    """向单个用户发送私信"""
    url = f"https://space.bilibili.com/{user_id}"

    try:
        # 访问用户主页
        print(f"[访问] {url}")
        driver.get(url)
        time.sleep(random.uniform(2, 4))

        # 查找"发消息"按钮
        try:
            msg_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '发消息')]"))
            )
        except:
            return {"status": "skip", "reason": "用户限制私信"}

        # 点击打开对话框
        msg_btn.click()
        time.sleep(random.uniform(1, 2))

        # 填写消息
        textarea = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
        )

        # 使用JavaScript输入
        driver.execute_script(f"arguments[0].value = arguments[1];", textarea, message)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)

        time.sleep(random.uniform(0.5, 1))

        # 点击发送
        send_btn = driver.find_element(By.XPATH, "//button[contains(text(), '发送')]")
        send_btn.click()
        time.sleep(2)

        return {"status": "success"}

    except Exception as e:
        return {"status": "failed", "reason": str(e)}

def main():
    print("\n" + "="*60)
    print("私信发送测试（第4-6位用户，跳过前3位）")
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

    # 显示将测试的用户（从第4位开始）
    start_index = 3
    test_count = 3
    print(f"\n测试用户（从第{start_index+1}位开始，测试{test_count}位）:")
    for idx in range(start_index, min(start_index + test_count, len(users))):
        user = users[idx]
        print(f"  {idx+1}. {user['nickname']} (ID: {user['user_id']}, 赞: {user['like_count']})")

    # 确认（自动确认）
    import sys
    print(f"\n[提示] 将依次测试第{start_index+1}-{start_index+test_count}位用户，直到发送成功或测试完")
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

        # 从第4位用户开始测试3位（跳过前3位）
        stats = {"success": 0, "skip": 0, "failed": 0}
        start_index = 3  # 从第4位用户开始（索引3）
        test_count = 3   # 测试3位用户

        for idx in range(start_index, min(start_index + test_count, len(users))):
            user = users[idx]
            print(f"\n{'='*60}")
            print(f"测试用户 {idx+1}/{len(users)}: {user['nickname']}")
            print(f"{'='*60}")

            result = send_message_to_user(driver, wait, user['user_id'], user['nickname'], message)

            if result['status'] == 'success':
                stats['success'] += 1
                print(f"  [OK] 发送成功！")
                print(f"\n[成功] 已成功发送给 {user['nickname']}！")
                break  # 发送成功，停止测试
            elif result['status'] == 'skip':
                stats['skip'] += 1
                print(f"  [SKIP] 跳过: {result['reason']}")
                print(f"  [继续] 尝试下一位用户...")
            else:
                stats['failed'] += 1
                print(f"  [FAIL] 失败: {result['reason']}")
                print(f"  [继续] 尝试下一位用户...")

            # 用户间延迟
            if idx < min(start_index + test_count, len(users)) - 1:
                print(f"\n[等待] 5秒后尝试下一位用户...")
                time.sleep(5)

        # 显示统计
        print(f"\n{'='*60}")
        print("测试完成")
        print(f"{'='*60}")
        print(f"成功: {stats['success']}")
        print(f"跳过: {stats['skip']}")
        print(f"失败: {stats['failed']}")

        if stats['success'] > 0:
            print(f"\n[OK] 测试成功！已成功发送私信")
        else:
            print(f"\n[提示] 测试的{test_count}位用户都限制私信或发送失败")

        # 等待查看结果
        print("\n[提示] 浏览器将保持打开30秒，请查看结果...")
        time.sleep(30)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
