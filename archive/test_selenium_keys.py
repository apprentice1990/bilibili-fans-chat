#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium真实键盘操作
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
    print("使用Selenium真实键盘操作")
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

    print(f"\n消息内容:")
    print("-"*60)
    print(message)
    print("-"*60)

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

        # 激活textarea
        print(f"\n[步骤1] 激活textarea...")
        driver.execute_script("""
            var textareas = document.querySelectorAll('textarea');
            var textarea = textareas[textareas.length - 1];

            // 激活
            var parent = textarea.parentElement;
            while (parent && parent.tagName !== 'BODY') {
                parent.style.display = '';
                parent.style.visibility = 'visible';
                parent = parent.parentElement;
            }

            textarea.style.display = 'block';
            textarea.style.visibility = 'visible';
            textarea.style.opacity = '1';
            textarea.scrollIntoView({block: 'center'});
            textarea.focus();
        """)

        time.sleep(1)

        # 使用Selenium输入消息
        print(f"\n[步骤2] 使用Selenium输入消息...")
        textarea = None
        try:
            textarea = driver.find_element(By.CSS_SELECTOR, "textarea")
        except:
            # 如果找不到，使用JavaScript查找
            textarea_ref = driver.execute_script("""
                var textareas = document.querySelectorAll('textarea');
                return textareas[textareas.length - 1];
            """)
            # 创建WebElement
            from selenium.webdriver.remote.webelement import WebElement
            # 这种方法不行，直接使用JavaScript输入
            driver.execute_script(f"""
                var textarea = document.querySelector('textarea');
                textarea.value = arguments[0];
                textarea.dispatchEvent(new Event('input', {{bubbles: true}}));
            """, message)
            print(f"  [OK] 已使用JavaScript输入")
            time.sleep(1)
        else:
            # 使用send_keys
            textarea.clear()
            textarea.send_keys(message)
            print(f"  [OK] 已使用send_keys输入")
            time.sleep(1)

        # 使用Selenium ActionChains发送Ctrl+Enter
        print(f"\n[步骤3] 使用Selenium发送Ctrl+Enter...")
        actions = ActionChains(driver)

        if textarea:
            # 确保聚焦
            actions.click(textarea).perform()
            time.sleep(0.5)

            # 发送Ctrl+Enter
            actions.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
            print(f"  [OK] 已发送Ctrl+Enter")
        else:
            # 使用JavaScript聚焦后发送
            driver.execute_script("""
                var textarea = document.querySelector('textarea');
                textarea.focus();
            """)
            time.sleep(0.5)

            # 直接对当前活动元素发送
            actions.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
            print(f"  [OK] 已发送Ctrl+Enter（到活动元素）")

        time.sleep(2)

        # 检查结果
        print(f"\n[步骤4] 检查结果...")
        result = driver.execute_script("""
            var textarea = document.querySelector('textarea');
            return {
                length: textarea ? textarea.value.length : -1,
                value: textarea ? textarea.value.substring(0, 50) : '',
                focused: document.activeElement === textarea
            };
        """)

        print(f"  输入框长度: {result.get('length')}")
        print(f"  是否聚焦: {result.get('focused')}")

        if result.get('length') == 0:
            print(f"\n  [SUCCESS] 消息已发送！")
        else:
            print(f"\n  [提示] 输入框仍有内容")
            print(f"  内容: {result.get('value')}...")

        # 保存截图
        screenshot_path = Path("debug_screenshots") / "selenium_keys_result.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"\n[截图] 已保存: {screenshot_path.name}")

        print("\n[提示] 浏览器将保持打开60秒，请查看...")
        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
