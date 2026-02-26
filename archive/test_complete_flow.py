#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整流程测试：包括点击用户选择
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
    print("完整流程测试")
    print("="*60)

    user_id = "96490197"
    nickname = "我们不能失去荔枝"

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

    print(f"\n消息内容:")
    print("-"*60)
    print(message)
    print("-"*60)

    if len(sys.argv) > 1 and sys.argv[1] != '--auto':
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

        # 步骤1: 检查页面状态
        print(f"\n[步骤1] 检查页面元素...")
        page_info = driver.execute_script("""
            return {
                textareas: document.querySelectorAll('textarea').length,
                buttons: document.querySelectorAll('button').length,
                lists: document.querySelectorAll('.list, [class*="list"], [class*="chat-list"]').length,
                bodyHTML: document.body.innerHTML.substring(0, 500)
            };
        """)
        print(f"  [调试] textarea: {page_info.get('textareas')}")
        print(f"  [调试] buttons: {page_info.get('buttons')}")
        print(f"  [调试] lists: {page_info.get('lists')}")

        # 步骤2: 尝试点击左侧用户列表（如果存在）
        print(f"\n[步骤2] 尝试点击左侧用户...")
        click_result = driver.execute_script("""
            // 查找所有可能包含用户信息的元素
            var allElements = document.querySelectorAll('*');
            var clicked = false;

            for (var i = 0; i < allElements.length; i++) {
                var text = allElements[i].textContent || '';
                // 查找包含目标用户昵称的元素
                if (text.indexOf('""" + nickname + """') !== -1 && text.length < 100) {
                    // 向上查找到可点击的父元素
                    var parent = allElements[i];
                    for (var j = 0; j < 5; j++) {
                        if (parent && parent.tagName === 'DIV' && parent.onclick) {
                            parent.click();
                            return {success: true, method: 'click-parent', tag: parent.tagName};
                        }
                        if (parent) parent = parent.parentElement;
                    }
                }
            }

            return {success: false, error: '未找到可点击的用户元素'};
        """)

        if click_result.get('success'):
            print(f"  [OK] 已点击用户元素 (方法: {click_result.get('method')})")
            time.sleep(2)
        else:
            print(f"  [SKIP] {click_result.get('error')}")

        # 步骤3: 点击输入框区域
        print(f"\n[步骤3] 点击输入框...")
        click_textarea = driver.execute_script("""
            var textareas = document.querySelectorAll('textarea');
            if (textareas.length > 0) {
                var textarea = textareas[textareas.length - 1];

                // 先滚动到可见区域
                textarea.scrollIntoView({block: 'center'});

                // 点击
                textarea.click();

                // 聚焦
                textarea.focus();

                // 再次点击确保
                textarea.click();

                return {
                    success: true,
                    focused: document.activeElement === textarea
                };
            }
            return {success: false};
        """)

        print(f"  [结果] 点击成功: {click_textarea.get('success')}, 聚焦: {click_textarea.get('focused')}")
        time.sleep(1)

        # 步骤4: 输入消息
        print(f"\n[步骤4] 输入消息...")
        input_result = driver.execute_script("""
            var message = arguments[0];
            var textareas = document.querySelectorAll('textarea');

            if (textareas.length === 0) return {success: false};

            var textarea = textareas[textareas.length - 1];

            // 使用setSelectionRange确保光标在末尾
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);

            // 模拟逐字输入
            for (var i = 0; i < message.length; i++) {
                var char = message[i];

                // 模拟keypress
                var keypressEvent = new KeyboardEvent('keypress', {
                    key: char,
                    code: 'Key' + char.toUpperCase(),
                    keyCode: char.charCodeAt(0),
                    which: char.charCodeAt(0),
                    bubbles: true
                });
                textarea.dispatchEvent(keypressEvent);

                // 模拟input
                var currentText = textarea.value + char;
                textarea.value = currentText;

                var inputEvent = new Event('input', { bubbles: true });
                textarea.dispatchEvent(inputEvent);
            }

            return {
                success: true,
                finalLength: textarea.value.length,
                finalValue: textarea.value.substring(0, 50)
            };
        """, message)

        print(f"  [结果] {input_result.get('success')}, 长度: {input_result.get('finalLength')}")
        print(f"  [内容] {input_result.get('finalValue')}...")
        time.sleep(1)

        # 步骤5: 尝试发送（查找并点击按钮）
        print(f"\n[步骤5] 查找发送按钮...")
        button_search = driver.execute_script("""
            var buttons = document.querySelectorAll('button');
            var result = {found: [], disabled: []};

            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.trim();
                var disabled = buttons[i].disabled;

                if (text && text.length < 20) {
                    if (disabled) {
                        result.disabled.push({index: i, text: text});
                    } else {
                        result.found.push({index: i, text: text, className: buttons[i].className});
                    }
                }
            }

            return result;
        """)

        print(f"  [调试] 可用按钮: {len(button_search.get('found', []))}")
        for btn in button_search.get('found', [])[:5]:
            print(f"    - [{btn.get('index')}] '{btn.get('text')}' class='{btn.get('className')[:30]}'")

        print(f"  [调试] 禁用按钮: {len(button_search.get('disabled', []))}")
        for btn in button_search.get('disabled', [])[:3]:
            print(f"    - [{btn.get('index')}] '{btn.get('text')}'")

        # 尝试点击所有包含"发送"的非禁用按钮
        sent = False
        for btn in button_search.get('found', []):
            if '发送' in btn.get('text', ''):
                print(f"\n  [尝试] 点击按钮: '{btn.get('text')}'")
                click_result = driver.execute_script("""
                    var buttons = document.querySelectorAll('button');
                    var index = arguments[0];
                    if (buttons[index]) {
                        buttons[index].click();
                        return {success: true};
                    }
                    return {success: false};
                """, btn.get('index'))

                if click_result.get('success'):
                    print(f"    [OK] 已点击")
                    sent = True
                    time.sleep(2)
                    break

        if not sent:
            # 最后尝试：使用回车键
            print(f"\n  [尝试] 使用Enter键发送...")
            driver.execute_script("""
                var textarea = document.querySelector('textarea');
                if (textarea) {
                    var enterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true
                    });
                    textarea.dispatchEvent(enterEvent);

                    // 也尝试Ctrl+Enter
                    var ctrlEnterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        ctrlKey: true
                    });
                    textarea.dispatchEvent(ctrlEnterEvent);
                }
            """)

        # 等待并检查
        time.sleep(3)

        # 检查输入框是否清空
        final_check = driver.execute_script("""
            var textarea = document.querySelector('textarea');
            return {
                value: textarea ? textarea.value : '',
                length: textarea ? textarea.value.length : 0
            };
        """)

        print(f"\n[最终检查] 输入框内容长度: {final_check.get('length')}")
        if final_check.get('length') == 0:
            print(f"  [OK] 输入框已清空，可能发送成功！")
        else:
            print(f"  [提示] 输入框仍有内容，可能未发送")

        # 保存截图
        screenshot_path = Path("debug_screenshots") / "complete_flow_result.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"\n[截图] 已保存: {screenshot_path.name}")

        print("\n[提示] 浏览器将保持打开60秒，请手动查看...")
        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
