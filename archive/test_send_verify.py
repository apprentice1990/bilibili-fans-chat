#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版发送脚本：添加验证步骤
"""

import pickle
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def main():
    print("\n" + "="*60)
    print("改进版发送测试（带验证）")
    print("="*60)

    # 测试用户
    user_id = "96490197"
    nickname = "我们不能失去荔枝"

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

    print(f"\n消息内容:")
    print("-"*60)
    print(message)
    print("-"*60)

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

        # 获取发送前的消息数量
        print(f"\n[步骤1] 检查发送前的消息数量...")
        before_count = driver.execute_script("""
            var messages = document.querySelectorAll('.list-item, .message-item, [class*="message"], [class*="chat"]');
            return messages.length;
        """)
        print(f"  [调试] 发送前消息数: {before_count}")

        # 使用JavaScript查找并激活textarea
        print(f"\n[步骤2] 查找并激活输入框...")
        textarea_info = driver.execute_script("""
            var textareas = document.querySelectorAll('textarea');
            if (textareas.length > 0) {
                var textarea = textareas[textareas.length - 1];

                // 滚动到输入框位置
                textarea.scrollIntoView({block: 'center', inline: 'center'});

                // 聚焦
                textarea.focus();
                textarea.click();

                return {
                    success: true,
                    length: textareas.length,
                    hasFocus: document.activeElement === textarea
                };
            }
            return {success: false};
        """)

        if not textarea_info.get('success'):
            print(f"  [FAIL] 未找到输入框")
            return

        print(f"  [OK] 找到输入框，已聚焦: {textarea_info.get('hasFocus')}")
        time.sleep(1)

        # 使用JavaScript填写消息（更可靠）
        print(f"\n[步骤3] 填写消息...")
        fill_result = driver.execute_script("""
            var message = arguments[0];

            var textareas = document.querySelectorAll('textarea');
            if (textareas.length === 0) {
                return {success: false, error: '未找到输入框'};
            }

            var textarea = textareas[textareas.length - 1];

            // 清空
            textarea.value = '';

            // 聚焦
            textarea.focus();

            // 设置值
            textarea.value = message;

            // 触发多个事件以确保被识别
            var events = ['input', 'change', 'keyup', 'keydown'];
            events.forEach(function(eventType) {
                var event = new Event(eventType, { bubbles: true, cancelable: true });
                textarea.dispatchEvent(event);
            });

            // 也触发React/Vue的输入事件
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            nativeInputValueSetter.call(textarea, message);

            var inputEvent = new Event('input', { bubbles: true });
            textarea.dispatchEvent(inputEvent);

            return {
                success: true,
                value: textarea.value,
                length: textarea.value.length
            };
        """, message)

        if not fill_result.get('success'):
            print(f"  [FAIL] {fill_result.get('error', '未知错误')}")
            return

        print(f"  [OK] 消息填写完成，长度: {fill_result.get('length')}")
        time.sleep(1)

        # 尝试多种发送方式
        print(f"\n[步骤4] 尝试发送...")

        # 方式1: 查找并点击发送按钮
        print(f"  [尝试1] 查找发送按钮...")
        button_click = driver.execute_script("""
            // 查找所有按钮
            var buttons = document.querySelectorAll('button, [role="button"], [class*="btn"]');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent || '';
                var cls = buttons[i].className || '';

                // 查找包含"发送"的按钮
                if (text.indexOf('发送') !== -1 && !buttons[i].disabled) {
                    buttons[i].click();
                    return {success: true, method: 'button-click', text: text};
                }

                // 查找class包含send的按钮
                if (cls.toLowerCase().indexOf('send') !== -1 && !buttons[i].disabled) {
                    buttons[i].click();
                    return {success: true, method: 'class-send', class: cls};
                }
            }
            return {success: false};
        """)

        if button_click.get('success'):
            print(f"    [OK] 使用按钮发送成功 (方法: {button_click.get('method')})")
        else:
            print(f"    [SKIP] 未找到可用的发送按钮")

            # 方式2: 使用Ctrl+Enter
            print(f"  [尝试2] 使用Ctrl+Enter...")
            try:
                textarea = driver.find_element(By.CSS_SELECTOR, "textarea")
                textarea.send_keys(Keys.CONTROL + Keys.ENTER)
                print(f"    [OK] 已发送Ctrl+Enter")
            except Exception as e:
                print(f"    [SKIP] Ctrl+Enter失败: {str(e)[:50]}")

                # 方式3: 使用JavaScript触发
                print(f"  [尝试3] 使用JavaScript触发...")
                js_result = driver.execute_script("""
                    var textarea = document.querySelector('textarea');
                    if (!textarea) return {success: false};

                    // 触发Enter事件
                    var enterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        ctrlKey: true,
                        cancelable: true
                    });
                    textarea.dispatchEvent(enterEvent);

                    // 也尝试不按Ctrl
                    var enterEvent2 = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true
                    });
                    textarea.dispatchEvent(enterEvent2);

                    return {success: true, method: 'js-events'};
                """)
                print(f"    [OK] JavaScript事件已触发")

        # 等待消息发送
        time.sleep(3)

        # 验证是否发送成功
        print(f"\n[步骤5] 验证发送结果...")
        after_count = driver.execute_script("""
            var messages = document.querySelectorAll('.list-item, .message-item, [class*="message"], [class*="chat"]');
            return messages.length;
        """)
        print(f"  [调试] 发送后消息数: {after_count}")

        # 检查输入框是否清空（成功的标志）
        textarea_value = driver.execute_script("""
            var textarea = document.querySelector('textarea');
            return textarea ? textarea.value : '';
        """)

        print(f"  [调试] 输入框内容长度: {len(textarea_value)}")
        if len(textarea_value) == 0:
            print(f"  [OK] 输入框已清空，可能发送成功")
        else:
            print(f"  [提示] 输入框仍有内容，可能未发送")
            print(f"  [内容] {textarea_value[:50]}...")

        # 查找消息记录
        print(f"\n[步骤6] 查找消息记录...")
        messages_found = driver.execute_script("""
            // 查找所有包含消息文本的元素
            var allElements = document.querySelectorAll('*');
            var messageElements = [];

            for (var i = 0; i < allElements.length; i++) {
                var text = allElements[i].textContent || '';
                // 查找包含我们发送的消息关键字的元素
                if (text.indexOf('你好') !== -1 || text.indexOf('感谢支持') !== -1) {
                    // 向上查找到消息容器
                    var parent = allElements[i];
                    for (var j = 0; j < 5; j++) {
                        if (parent && (parent.className.indexOf('message') !== -1 ||
                                     parent.className.indexOf('chat') !== -1 ||
                                     parent.className.indexOf('item') !== -1)) {
                            messageElements.push({
                                tag: parent.tagName,
                                className: parent.className,
                                text: parent.textContent.substring(0, 50)
                            });
                            break;
                        }
                        parent = parent.parentElement;
                    }
                }
            }

            return messageElements;
        """)

        if messages_found:
            print(f"  [OK] 找到 {len(messages_found)} 条可能的消息记录:")
            for idx, msg in enumerate(messages_found[:3]):
                print(f"    {idx+1}. tag={msg.get('tag')}, class={msg.get('className')[:30]}")
                print(f"       内容: {msg.get('text')}")
        else:
            print(f"  [提示] 未找到消息记录")

        # 保存最终截图
        screenshot_path = Path("debug_screenshots") / "final_result.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"\n[截图] 已保存: {screenshot_path.name}")

        print("\n[提示] 浏览器将保持打开60秒，请手动确认...")
        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
