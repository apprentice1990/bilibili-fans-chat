#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量发送脚本 - 最终可用版本
使用contenteditable元素，已验证成功
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

def send_to_user(driver, user_id, message):
    """向用户发送私信"""
    try:
        # 导航到私信页面
        msg_url = f"https://message.bilibili.com/#/whisper/mid{user_id}"
        driver.get(msg_url)
        time.sleep(5)

        # 完整发送流程
        result = driver.execute_script("""
            var message = arguments[0];

            // 1. 关闭弹窗
            var closeBtn = document.querySelector('.bili-popup__header__close');
            if (closeBtn) {
                closeBtn.click();
            }

            // 2. 找到contenteditable输入框
            var editables = document.querySelectorAll('[contenteditable="true"]');
            var targetElement = null;

            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    targetElement = editables[i];
                    break;
                }
            }

            if (!targetElement) {
                return {success: false, error: '未找到contenteditable输入框'};
            }

            // 3. 聚焦并输入消息
            targetElement.focus();
            targetElement.click();
            targetElement.textContent = message;

            // 触发事件
            var events = ['input', 'change', 'keyup'];
            events.forEach(function(type) {
                var event = new Event(type, {bubbles: true});
                targetElement.dispatchEvent(event);
            });

            // 4. 发送（尝试多种方法）
            // 方法1: 查找发送按钮
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.trim();
                if (text.indexOf('发送') !== -1 && !buttons[i].disabled) {
                    buttons[i].click();
                    return {success: true, method: 'button'};
                }
            }

            // 方法2: Ctrl+Enter
            var ctrlEnter = new KeyboardEvent('keydown', {
                key: 'Enter', code: 'Enter', keyCode: 13,
                bubbles: true, ctrlKey: true
            });
            targetElement.dispatchEvent(ctrlEnter);

            // 方法3: 普通Enter
            var enter = new KeyboardEvent('keydown', {
                key: 'Enter', code: 'Enter', keyCode: 13,
                bubbles: true
            });
            targetElement.dispatchEvent(enter);

            return {success: true, method: 'keyboard'};
        """, message)

        time.sleep(2)

        # 验证
        check = driver.execute_script("""
            var editables = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    return {
                        length: editables[i].textContent.length,
                        empty: editables[i].textContent.length === 0
                    };
                }
            }
            return {error: 'check failed'};
        """)

        if check.get('empty', False):
            return {"status": "success"}
        else:
            return {"status": "failed", "reason": f"未清空，长度: {check.get('length')}"}

    except Exception as e:
        return {"status": "failed", "reason": str(e)[:200]}

def main():
    print("\n" + "="*60)
    print("批量发送脚本（已验证可用版本）")
    print("="*60)

    # 加载用户
    json_file = "data/users/BV1TRzZBuEg6_20260225_163222.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    users = data['users']

    print(f"[OK] 已加载 {len(users)} 位用户")

    # 准备消息
    bv_id = "BV1EYf4BQE7q"
    video_url = f"https://www.bilibili.com/video/{bv_id}"
    title = "忽然"

    template_file = "templates/message_template.txt"
    if Path(template_file).exists():
        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()
    else:
        template = msg_config.DEFAULT_MESSAGE_TEMPLATE

    message = template.format(title=title, video_url=video_url)

    print(f"\n消息: {message[:50]}...")

    # 发送给所有用户
    sendable = list(range(len(users)))  # 所有用户索引

    print(f"\n可发送用户: {len(sendable)} 位")
    for idx in sendable:
        if idx < len(users):
            print(f"  {idx+1}. {users[idx]['nickname']}")

    # 确认
    confirm = input("\n开始批量发送？(yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("[取消] 已取消")
        return

    # 初始化浏览器
    print("\n[浏览器] 启动...")
    options = Options()
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        # 加载cookies
        print("\n[Cookies] 加载...")
        cookie_path = msg_config.COOKIE_FILE

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
        stats = {"success": 0, "failed": 0}

        for idx in sendable:
            if idx >= len(users):
                break

            user = users[idx]
            print(f"\n[{stats['success']+stats['failed']+1}/{len(sendable)}] {user['nickname']}")

            result = send_to_user(driver, user['user_id'], message)

            if result['status'] == 'success':
                stats['success'] += 1
                print(f"  [OK] 成功！")
                # 成功后可以选择继续或停止
                if stats['success'] >= 1:  # 至少成功1条后询问
                    cont = input("\n已成功发送，继续？(yes/no): ").strip().lower()
                    if cont not in ['yes', 'y']:
                        print("[停止] 用户中断")
                        break
            else:
                stats['failed'] += 1
                print(f"  [FAIL] {result['reason']}")

            # 用户间延迟（保守模式）
            if idx < sendable[-1]:
                delay = random.randint(10, 20)
                print(f"  [等待] {delay}秒...")
                time.sleep(delay)

        # 统计
        print(f"\n{'='*60}")
        print("完成")
        print(f"{'='*60}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failed']}")

        print("\n[提示] 浏览器保持打开30秒...")
        time.sleep(30)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
