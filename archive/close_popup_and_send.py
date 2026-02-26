#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关闭弹窗并查找真正的输入框
"""

import pickle
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def main():
    print("\n" + "="*60)
    print("关闭弹窗并发送消息")
    print("="*60)

    user_id = "331613"

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

        # 导航到私信页面
        msg_url = f"https://message.bilibili.com/#/whisper/mid{user_id}"
        print(f"\n[访问] {msg_url}")
        driver.get(msg_url)
        time.sleep(5)

        # 步骤1: 检查并关闭弹窗
        print("\n[步骤1] 检查弹窗...")
        popup_check = driver.execute_script("""
            var popups = document.querySelectorAll('.bili-popup, [class*="popup"], [class*="modal"]');
            return {
                count: popups.length,
                hasPopup: popups.length > 0
            };
        """)

        print(f"  弹窗数量: {popup_check.get('count')}")

        if popup_check.get('hasPopup'):
            print("  [关闭] 尝试关闭弹窗...")

            # 尝试点击关闭按钮
            close_result = driver.execute_script("""
                // 查找关闭按钮
                var closeBtn = document.querySelector('.bili-popup__header__close, .close, [class*="close"]');
                if (closeBtn) {
                    closeBtn.click();
                    return {method: 'click-close', success: true};
                }

                // 按ESC键关闭
                var escEvent = new KeyboardEvent('keydown', {
                    key: 'Escape',
                    code: 'Escape',
                    keyCode: 27,
                    bubbles: true
                });
                document.dispatchEvent(escEvent);
                return {method: 'escape-key', success: true};

                // 移除弹窗元素
                var popups = document.querySelectorAll('.bili-popup, [class*="popup"]');
                for (var i = 0; i < popups.length; i++) {
                    popups[i].style.display = 'none';
                }
                return {method: 'hide-popup', success: true};
            """)

            print(f"    {close_result.get('method')}: {close_result.get('success')}")
            time.sleep(2)

        # 步骤2: 再次探测元素
        print("\n[步骤2] 探测输入元素...")
        element_check = driver.execute_script("""
            var result = {
                textareas: [],
                editables: [],
                inputs: []
            };

            // Textarea
            var textareas = document.querySelectorAll('textarea');
            for (var i = 0; i < textareas.length; i++) {
                var rect = textareas[i].getBoundingClientRect();
                result.textareas.push({
                    index: i,
                    w: rect.width,
                    h: rect.height,
                    vis: rect.width > 0 && rect.height > 0
                });
            }

            // ContentEditable
            var editables = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                result.editables.push({
                    index: i,
                    tag: editables[i].tagName,
                    w: rect.width,
                    h: rect.height,
                    vis: rect.width > 0 && rect.height > 0
                });
            }

            // Inputs
            var inputs = document.querySelectorAll('input[type="text"], input:not([type])');
            for (var i = 0; i < inputs.length; i++) {
                var rect = inputs[i].getBoundingClientRect();
                result.inputs.push({
                    index: i,
                    w: rect.width,
                    h: rect.height,
                    vis: rect.width > 0 && rect.height > 0
                });
            }

            return result;
        """)

        print(f"  Textarea: {len(element_check.get('textareas', []))}")
        for ta in element_check.get('textareas', []):
            print(f"    [{ta.get('index')}] {ta.get('w')}x{ta.get('h')} visible={ta.get('vis')}")

        print(f"  ContentEditable: {len(element_check.get('editables', []))}")
        for ed in element_check.get('editables', []):
            print(f"    [{ed.get('index')}] {ed.get('tag')} {ed.get('w')}x{ed.get('h')} visible={ed.get('vis')}")

        print(f"  Inputs: {len(element_check.get('inputs', []))}")
        for inp in element_check.get('inputs', []):
            print(f"    [{inp.get('index')}] {inp.get('w')}x{inp.get('h')} visible={inp.get('vis')}")

        # 步骤3: 尝试在可见元素中输入
        print("\n[步骤3] 尝试输入消息...")

        # 查找第一个可见的可输入元素
        input_success = driver.execute_script("""
            var message = arguments[0];

            // 尝试contenteditable
            var editables = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    editables[i].focus();
                    editables[i].click();
                    editables[i].textContent = message;

                    var inputEvent = new Event('input', {bubbles: true});
                    editables[i].dispatchEvent(inputEvent);

                    return {success: true, type: 'contenteditable', index: i};
                }
            }

            // 尝试visible textarea
            var textareas = document.querySelectorAll('textarea');
            for (var i = 0; i < textareas.length; i++) {
                var rect = textareas[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    textareas[i].focus();
                    textareas[i].click();
                    textareas[i].value = message;

                    var inputEvent = new Event('input', {bubbles: true});
                    textareas[i].dispatchEvent(inputEvent);

                    return {success: true, type: 'textarea', index: i};
                }
            }

            // 尝试visible input
            var inputs = document.querySelectorAll('input[type="text"], input:not([type])');
            for (var i = 0; i < inputs.length; i++) {
                var rect = inputs[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && !inputs[i].disabled) {
                    inputs[i].focus();
                    inputs[i].value = message;

                    var inputEvent = new Event('input', {bubbles: true});
                    inputs[i].dispatchEvent(inputEvent);

                    return {success: true, type: 'input', index: i};
                }
            }

            return {success: false, error: '未找到可输入元素'};
        """, message)

        if input_success.get('success'):
            print(f"  [OK] 输入成功! 类型: {input_success.get('type')}, 索引: {input_success.get('index')}")
            time.sleep(1)

            # 保存截图
            screenshot = Path("debug_screenshots") / "after_input.png"
            driver.save_screenshot(str(screenshot))
            print(f"\n[截图] 已保存: {screenshot.name}")
            print(f"\n[提示] 浏览器保持打开60秒，请查看并手动发送...")
            time.sleep(60)
        else:
            print(f"  [FAIL] {input_success.get('error')}")

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
