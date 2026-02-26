#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查textarea状态并找到正确的操作方法
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
    print("检查textarea状态")
    print("="*60)

    user_id = "331613"

    # 初始化浏览器
    print("\n[浏览器] 初始化中...")
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

        # 详细检查textarea
        print(f"\n[检查] textarea详细信息...")
        textarea_info = driver.execute_script("""
            var textareas = document.querySelectorAll('textarea');
            if (textareas.length === 0) return {error: '未找到textarea'};

            var textarea = textareas[textareas.length - 1];
            var rect = textarea.getBoundingClientRect();

            // 获取计算样式
            var style = window.getComputedStyle(textarea);

            // 查找父元素
            var parent = textarea.parentElement;
            var parentInfo = null;
            if (parent) {
                var parentRect = parent.getBoundingClientRect();
                var parentStyle = window.getComputedStyle(parent);
                parentInfo = {
                    tag: parent.tagName,
                    display: parentStyle.display,
                    visibility: parentStyle.visibility,
                    width: parentRect.width,
                    height: parentRect.height
                };
            }

            return {
                found: true,
                count: textareas.length,
                value: textarea.value,
                valueLength: textarea.value.length,
                disabled: textarea.disabled,
                readOnly: textarea.readOnly,
                rect: {
                    top: rect.top,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height,
                    isEmpty: rect.width === 0 || rect.height === 0
                },
                style: {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    zIndex: style.zIndex
                },
                parent: parentInfo,
                focused: document.activeElement === textarea
            };
        """)

        print(f"  找到textarea数量: {textarea_info.get('count')}")
        print(f"  值长度: {textarea_info.get('valueLength')}")
        print(f"  是否禁用: {textarea_info.get('disabled')}")
        print(f"  是否只读: {textarea_info.get('readOnly')}")
        print(f"  是否聚焦: {textarea_info.get('focused')}")

        rect = textarea_info.get('rect', {})
        print(f"  尺寸: {rect.get('width')} x {rect.get('height')}")
        print(f"  是否为空: {rect.get('isEmpty')}")

        style = textarea_info.get('style', {})
        print(f"  display: {style.get('display')}")
        print(f"  visibility: {style.get('visibility')}")
        print(f"  opacity: {style.get('opacity')}")

        if textarea_info.get('parent'):
            parent = textarea_info.get('parent')
            print(f"\n  父元素:")
            print(f"    tag: {parent.get('tag')}")
            print(f"    display: {parent.get('display')}")
            print(f"    尺寸: {parent.get('width')} x {parent.get('height')}")

        # 尝试激活textarea
        print(f"\n[尝试] 激活textarea...")
        activate_result = driver.execute_script("""
            var textareas = document.querySelectorAll('textarea');
            if (textareas.length === 0) return {success: false};

            var textarea = textareas[textareas.length - 1];

            // 1. 先确保父元素可见
            var parent = textarea.parentElement;
            while (parent && parent.tagName !== 'BODY') {
                parent.style.display = '';
                parent.style.visibility = 'visible';
                parent.style.opacity = '1';
                parent = parent.parentElement;
            }

            // 2. 设置textarea样式
            textarea.style.display = 'block';
            textarea.style.visibility = 'visible';
            textarea.style.opacity = '1';
            textarea.style.width = '100%';
            textarea.style.height = '50px';

            // 3. 滚动到视图
            textarea.scrollIntoView({block: 'center', inline: 'center'});

            // 4. 聚焦
            textarea.focus();
            textarea.click();

            // 5. 检查新状态
            var newRect = textarea.getBoundingClientRect();

            return {
                success: true,
                newWidth: newRect.width,
                newHeight: newRect.height,
                focused: document.activeElement === textarea
            };
        """)

        print(f"  激活后尺寸: {activate_result.get('newWidth')} x {activate_result.get('newHeight')}")
        print(f"  激活后聚焦: {activate_result.get('focused')}")

        time.sleep(2)

        # 再次尝试输入
        print(f"\n[尝试] 输入测试消息...")
        test_msg = "你好，这是一条测试消息"
        input_result = driver.execute_script("""
            var message = arguments[0];
            var textareas = document.querySelectorAll('textarea');
            var textarea = textareas[textareas.length - 1];

            // 聚焦
            textarea.focus();

            // 设置值
            textarea.value = message;

            // 触发事件
            var events = ['focus', 'input', 'change', 'blur'];
            events.forEach(function(type) {
                var event = new Event(type, {bubbles: true});
                textarea.dispatchEvent(event);
            });

            return {
                success: true,
                value: textarea.value,
                length: textarea.value.length
            };
        """, test_msg)

        print(f"  输入结果: {input_result.get('success')}")
        print(f"  值长度: {input_result.get('length')}")
        print(f"  内容: {input_result.get('value')}")

        # 保存截图
        screenshot_path = Path("debug_screenshots") / "textarea_check.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"\n[截图] 已保存: {screenshot_path.name}")

        print("\n[提示] 浏览器将保持打开60秒...")
        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
