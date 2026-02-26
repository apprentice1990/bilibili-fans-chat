#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动发送助手：输入消息后保持页面打开
"""

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

def main():
    print("\n" + "="*60)
    print("手动发送助手")
    print("="*60)

    # 使用用户5（风雨中年人）
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

    print(f"\n消息内容:")
    print("-"*60)
    print(message)
    print("-"*60)
    print(f"\n目标用户ID: {user_id}")
    print(f"页面URL: https://message.bilibili.com/#/whisper/mid{user_id}")

    confirm = input("\n准备好开始？(yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("[取消] 已取消")
        return

    # 初始化浏览器
    print("\n[浏览器] 启动中...")
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

        # 激活textarea
        print(f"\n[激活] 输入框...")
        activate_result = driver.execute_script("""
            var textareas = document.querySelectorAll('textarea');
            if (textareas.length === 0) return {success: false};

            var textarea = textareas[textareas.length - 1];

            // 激活父元素
            var parent = textarea.parentElement;
            while (parent && parent.tagName !== 'BODY') {
                parent.style.display = '';
                parent.style.visibility = 'visible';
                parent = parent.parentElement;
            }

            // 设置textarea样式
            textarea.style.display = 'block';
            textarea.style.visibility = 'visible';
            textarea.style.opacity = '1';

            // 滚动到视图
            textarea.scrollIntoView({block: 'center'});

            // 聚焦
            textarea.focus();
            textarea.click();

            return {
                success: true,
                activated: true
            };
        """)

        if activate_result.get('success'):
            print(f"  [OK] 输入框已激活")
        else:
            print(f"  [FAIL] 激活失败")

        time.sleep(1)

        # 输入消息
        print(f"\n[输入] 消息内容...")
        input_result = driver.execute_script("""
            var message = arguments[0];
            var textareas = document.querySelectorAll('textarea');
            var textarea = textareas[textareas.length - 1];

            // 清空并输入
            textarea.value = '';

            // 逐字模拟输入（更真实）
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

                // 更新值
                textarea.value = textarea.value + char;

                // 触发input事件
                var inputEvent = new Event('input', {bubbles: true});
                textarea.dispatchEvent(inputEvent);
            }

            // 最后触发change事件
            var changeEvent = new Event('change', {bubbles: true});
            textarea.dispatchEvent(changeEvent);

            return {
                success: true,
                length: textarea.value.length
            };
        """, message)

        if input_result.get('success'):
            print(f"  [OK] 消息已输入，长度: {input_result.get('length')}")
        else:
            print(f"  [FAIL] 输入失败")

        time.sleep(1)

        # 检查按钮状态
        print(f"\n[检查] 发送按钮状态...")
        button_check = driver.execute_script("""
            var buttons = document.querySelectorAll('button');
            var result = [];

            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.trim();
                var disabled = buttons[i].disabled;
                if (text && text.length < 30) {
                    result.push({
                        index: i,
                        text: text,
                        disabled: disabled,
                        className: buttons[i].className
                    });
                }
            }

            return result;
        """)

        print(f"  按钮列表:")
        for btn in button_check:
            status = "[OK]" if not btn.get('disabled') else "[禁用]"
            print(f"    [{btn.get('index')}] '{btn.get('text')}' - {status}")

        print(f"\n{'='*60}")
        print(f"[完成] 消息已输入到对话框！")
        print(f"{'='*60}")
        print(f"\n现在您可以:")
        print(f"  1. 在浏览器中查看输入框中的消息")
        print(f"  2. 手动点击发送按钮")
        print(f"  3. 或者尝试按 Ctrl+Enter 发送")
        print(f"\n浏览器将保持打开10分钟...")

        # 保持浏览器打开10分钟
        time.sleep(600)  # 10分钟 = 600秒

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
