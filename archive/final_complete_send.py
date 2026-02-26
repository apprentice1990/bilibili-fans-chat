#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终完整发送脚本 - 使用contenteditable
"""

import json
import pickle
import time
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

        # 步骤1: 关闭弹窗
        driver.execute_script("""
            // 点击关闭按钮
            var closeBtn = document.querySelector('.bili-popup__header__close, .close');
            if (closeBtn) {
                closeBtn.click();
            }
        """)
        time.sleep(1)

        # 步骤2: 输入消息到contenteditable
        input_result = driver.execute_script("""
            var message = arguments[0];

            // 查找contenteditable元素
            var editables = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    // 聚焦并点击
                    editables[i].focus();
                    editables[i].click();

                    // 设置消息
                    editables[i].textContent = message;

                    // 触发事件
                    var events = ['input', 'change', 'keyup'];
                    events.forEach(function(type) {
                        var event = new Event(type, {bubbles: true});
                        editables[i].dispatchEvent(event);
                    });

                    return {success: true, index: i};
                }
            }

            return {success: false, error: '未找到可输入元素'};
        """, message)

        if not input_result.get('success'):
            return {"status": "failed", "reason": input_result.get('error')}

        time.sleep(1)

        # 步骤3: 发送（查找发送按钮或使用Enter）
        send_result = driver.execute_script("""
            // 查找所有按钮
            var buttons = document.querySelectorAll('button');

            // 尝试找到发送按钮
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.trim();
                if (text.indexOf('发送') !== -1 && !buttons[i].disabled) {
                    buttons[i].click();
                    return {success: true, method: 'button'};
                }
            }

            // 尝试Enter键
            var editables = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    editables[i].focus();

                    // Ctrl+Enter
                    var ctrlEnter = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        bubbles: true,
                        ctrlKey: true
                    });
                    editables[i].dispatchEvent(ctrlEnter);

                    // 普通Enter
                    var enter = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        bubbles: true
                    });
                    editables[i].dispatchEvent(enter);

                    return {success: true, method: 'enter-key'};
                }
            }

            return {success: false, error: '无法发送'};
        """)

        time.sleep(2)

        # 检查结果
        check = driver.execute_script("""
            var editables = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    return {
                        textLength: editables[i].textContent.length,
                        isEmpty: editables[i].textContent.length === 0
                    };
                }
            }
            return {error: '未找到输入框'};
        """)

        if check.get('isEmpty', False):
            return {"status": "success"}
        else:
            return {"status": "failed", "reason": f"消息未发送，长度: {check.get('textLength')}"}

    except Exception as e:
        return {"status": "failed", "reason": str(e)[:200]}

def main():
    print("\n" + "="*60)
    print("完整发送脚本（contenteditable版）")
    print("="*60)

    # 加载用户列表
    json_file = "data/users/BV1TRzZBuEg6_20260225_163222.json"

    if not Path(json_file).exists():
        print(f"[错误] 文件不存在: {json_file}")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    users = data['users']

    print(f"[OK] 已加载 {len(users)} 位用户")

    # 准备消息
    bv_id = "BV1TRzZBuEg6"
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

    # 测试用户5-10
    test_users = [4, 5, 6, 7, 8, 9]  # 索引4-9对应5-10

    print(f"\n测试用户 {len(test_users)} 位")

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

        # 逐个测试
        stats = {"success": 0, "failed": 0}

        for idx in test_users:
            if idx >= len(users):
                break

            user = users[idx]
            print(f"\n{'='*60}")
            print(f"测试 {idx+1}/{len(users)}: {user['nickname']}")
            print(f"{'='*60}")

            result = send_to_user(driver, user['user_id'], message)

            if result['status'] == 'success':
                stats['success'] += 1
                print(f"  [OK] 发送成功！")
                print(f"\n{'='*60}")
                print(f"[SUCCESS] 已成功向 {user['nickname']} 发送私信！")
                print(f"{'='*60}")
                break
            else:
                stats['failed'] += 1
                reason = result.get('reason', '未知错误')
                print(f"  [FAIL] {reason}")

            # 用户间延迟
            time.sleep(3)

        # 统计
        print(f"\n{'='*60}")
        print("完成")
        print(f"{'='*60}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failed']}")

        # 保持打开30秒
        print("\n[提示] 浏览器保持打开30秒...")
        time.sleep(30)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
