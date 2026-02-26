#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：直接访问私信页面
"""

import pickle
import time
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

def main():
    print("\n" + "="*60)
    print("测试：直接访问私信页面")
    print("="*60)

    # 测试用户4
    user_id = "96490197"
    nickname = "我们不能失去荔枝"

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

    print(f"\n测试用户:")
    print(f"  昵称: {nickname}")
    print(f"  ID: {user_id}")

    # 确认
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

        # 直接导航到私信页面
        # B站私信URL格式: https://message.bilibili.com/#/whisper/mid{user_id}
        msg_url = f"https://message.bilibili.com/#/whisper/mid{user_id}"
        print(f"\n[访问] 私信页面: {msg_url}")
        driver.get(msg_url)
        time.sleep(5)

        # 保存截图
        screenshot_path = Path("debug_screenshots") / "direct_message_page.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"  [截图] 已保存: {screenshot_path.name}")

        # 查找并填写输入框
        print(f"\n[步骤1] 查找消息输入框...")
        try:
            # 等待页面加载
            time.sleep(5)

            # 使用JavaScript填写消息
            fill_result = driver.execute_script("""
                var message = arguments[0];

                // 优先查找textarea
                var textareas = document.querySelectorAll('textarea');
                if (textareas.length > 0) {
                    var textarea = textareas[textareas.length - 1]; // 使用最后一个
                    textarea.value = message;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    return {success: true, type: 'textarea', length: textareas.length};
                }

                // 尝试contenteditable
                var editables = document.querySelectorAll('[contenteditable="true"]');
                if (editables.length > 0) {
                    var editable = editables[editables.length - 1];
                    editable.textContent = message;
                    editable.dispatchEvent(new Event('input', { bubbles: true }));
                    return {success: true, type: 'contenteditable', length: editables.length};
                }

                return {success: false, error: '未找到输入框'};
            """, message)

            if not fill_result.get('success'):
                print(f"  [FAIL] {fill_result.get('error', '未知错误')}")
            else:
                print(f"  [OK] 消息填写成功 (类型: {fill_result.get('type')})")
                time.sleep(1)

                # 点击发送按钮
                print(f"\n[步骤2] 查找发送按钮...")
                button_info = driver.execute_script("""
                    // 收集所有按钮信息
                    var buttons = document.querySelectorAll('button');
                    var result = {
                        totalButtons: buttons.length,
                        buttons: []
                    };

                    for (var i = 0; i < buttons.length; i++) {
                        result.buttons.push({
                            index: i,
                            text: buttons[i].textContent.trim(),
                            className: buttons[i].className,
                            disabled: buttons[i].disabled
                        });
                    }

                    return result;
                """)

                print(f"  [调试] 总共找到 {button_info.get('totalButtons')} 个按钮")
                print(f"  [调试] 按钮列表:")
                for btn in button_info.get('buttons', [])[:10]:
                    text = btn.get('text', '')[:20]
                    cls = btn.get('className', '')[:30]
                    disabled = ' (禁用)' if btn.get('disabled') else ''
                    print(f"    [{btn.get('index')}] text='{text}' class='{cls}'{disabled}")

                # 现在尝试点击
                print(f"\n[步骤3] 尝试点击发送按钮...")
                send_result = driver.execute_script("""
                    // 查找包含"发送"文本的按钮
                    var buttons = document.querySelectorAll('button');
                    for (var i = 0; i < buttons.length; i++) {
                        var text = buttons[i].textContent.trim();
                        if (text.indexOf('发送') !== -1 && !buttons[i].disabled) {
                            buttons[i].click();
                            return {success: true, text: text, method: 'text-match'};
                        }
                    }

                    // 尝试使用Enter键发送
                    var textarea = document.querySelector('textarea');
                    if (textarea) {
                        var event = new KeyboardEvent('keydown', {
                            key: 'Enter',
                            code: 'Enter',
                            which: 13,
                            keyCode: 13,
                            bubbles: true,
                            ctrlKey: true  // Ctrl+Enter发送
                        });
                        textarea.dispatchEvent(event);
                        return {success: true, text: 'Ctrl+Enter', method: 'keyboard'};
                    }

                    return {success: false, error: '未找到发送按钮'};
                """)

                if send_result.get('success'):
                    print(f"  [OK] 发送成功！(方法: {send_result.get('method')}, 按钮/按键: {send_result.get('text')})")
                    time.sleep(3)
                    print(f"\n{'='*60}")
                    print(f"[SUCCESS] 私信发送成功！")
                    print(f"{'='*60}")
                else:
                    print(f"  [FAIL] {send_result.get('error', '未知错误')}")

        except Exception as e:
            print(f"  [FAIL] 发送失败: {str(e)[:200]}")
            import traceback
            traceback.print_exc()

        # 等待查看结果
        print("\n[提示] 浏览器将保持打开60秒，请查看结果...")
        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
