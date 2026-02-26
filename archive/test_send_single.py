#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：向单个用户发送私信
使用已获取的用户列表进行测试
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

def send_message_to_user(driver, user_id, message):
    """向单个用户发送私信"""
    url = f"https://space.bilibili.com/{user_id}"

    try:
        # 访问用户主页
        print(f"[访问] {url}")
        driver.get(url)
        time.sleep(random.uniform(2, 4))

        # 查找"发消息"按钮
        try:
            msg_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '发消息')]"))
            )
        except:
            return {"status": "skip", "reason": "用户限制私信"}

        # 点击打开对话框
        msg_btn.click()
        time.sleep(random.uniform(1, 2))

        # 填写消息
        textarea = WebDriverWait(driver, 10).until(
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
    print("私信发送测试（单用户）")
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

    # 显示第一个用户
    user = users[0]
    print(f"\n测试用户:")
    print(f"  昵称: {user['nickname']}")
    print(f"  ID: {user['user_id']}")
    print(f"  评论: {user['comment']}")
    print(f"  点赞: {user['like_count']}")

    # 确认
    confirm = input("\n确认发送？(yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("[取消] 已取消")
        return

    # 初始化浏览器
    print("\n[浏览器] 初始化中...")
    options = Options()
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')
    options.add_experimental_option('useAutomationExtension', False)

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

        # 发送消息
        print(f"\n[发送] 向 {user['nickname']} 发送私信...")
        result = send_message_to_user(driver, user['user_id'], message)

        if result['status'] == 'success':
            print(f"\n✓ 发送成功！")
        elif result['status'] == 'skip':
            print(f"\n→ 跳过: {result['reason']}")
        else:
            print(f"\n✗ 失败: {result['reason']}")

        # 等待查看结果
        print("\n[提示] 浏览器将保持打开30秒，请查看结果...")
        time.sleep(30)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
