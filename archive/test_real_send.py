#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试：使用真实的键盘事件
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
    print("最终测试：使用真实键盘事件")
    print("="*60)

    user_id = "331613"  # 用户5：风雨中年人

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

    print(f"\n测试用户ID: {user_id}")

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

        # 方法：使用Selenium的ActionChains模拟真实用户操作
        print(f"\n[步骤1] 查找并点击textarea...")
        try:
            textarea = driver.find_element(By.CSS_SELECTOR, "textarea")

            # 滚动到可见区域
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
            time.sleep(0.5)

            # 点击并聚焦
            actions = ActionChains(driver)
            actions.move_to_element(textarea).click().perform()
            time.sleep(0.5)

            print(f"  [OK] 已点击textarea")

        except Exception as e:
            print(f"  [FAIL] {str(e)[:100]}")
            return

        # 清空并输入消息
        print(f"\n[步骤2] 输入消息...")
        try:
            textarea = driver.find_element(By.CSS_SELECTOR, "textarea")
            textarea.clear()

            # 使用send_keys逐字输入（最真实）
            for char in message:
                textarea.send_keys(char)
                time.sleep(0.01)  # 小延迟模拟真实输入

            print(f"  [OK] 消息输入完成")
            time.sleep(1)

        except Exception as e:
            print(f"  [FAIL] {str(e)[:100]}")
            return

        # 检查按钮状态
        print(f"\n[步骤3] 检查发送按钮状态...")
        button_status = driver.execute_script("""
            var buttons = document.querySelectorAll('button');
            var result = [];
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.trim();
                if (text && text.length < 30) {
                    result.push({
                        index: i,
                        text: text,
                        disabled: buttons[i].disabled,
                        className: buttons[i].className
                    });
                }
            }
            return result;
        """)

        print(f"  按钮状态:")
        for btn in button_status:
            status = "禁用" if btn.get('disabled') else "可用"
            print(f"    [{btn.get('index')}] '{btn.get('text')}' - {status}")

        # 尝试发送
        print(f"\n[步骤4] 尝试发送...")

        # 方法1: 查找并发送按钮
        sent = False
        for btn in button_status:
            if not btn.get('disabled') and '发送' in btn.get('text', ''):
                print(f"  [尝试1] 点击发送按钮...")
                try:
                    send_btn = driver.find_elements(By.TAG_NAME, "button")[btn.get('index')]
                    send_btn.click()
                    print(f"    [OK] 已点击")
                    sent = True
                    time.sleep(2)
                    break
                except:
                    pass

        # 方法2: 如果没找到按钮，使用Ctrl+Enter
        if not sent:
            print(f"  [尝试2] 使用Ctrl+Enter...")
            try:
                textarea = driver.find_element(By.CSS_SELECTOR, "textarea")

                # 确保聚焦
                actions = ActionChains(driver)
                actions.click(textarea).perform()
                time.sleep(0.5)

                # 发送Ctrl+Enter
                actions.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
                print(f"    [OK] 已发送Ctrl+Enter")
                time.sleep(2)

            except Exception as e:
                print(f"    [FAIL] {str(e)[:100]}")

                # 方法3: 纯Enter
                print(f"  [尝试3] 使用Enter...")
                try:
                    textarea.send_keys(Keys.ENTER)
                    print(f"    [OK] 已发送Enter")
                    time.sleep(2)
                except Exception as e2:
                    print(f"    [FAIL] {str(e2)[:100]}")

        # 验证
        print(f"\n[步骤5] 验证结果...")
        final_check = driver.execute_script("""
            var textarea = document.querySelector('textarea');
            return {
                value: textarea ? textarea.value : '',
                length: textarea ? textarea.value.length : 0
            };
        """)

        print(f"  输入框内容长度: {final_check.get('length')}")
        if final_check.get('length') == 0:
            print(f"  [成功] 输入框已清空！")
        else:
            print(f"  [提示] 仍有内容，未发送")

        # 保存截图
        screenshot_path = Path("debug_screenshots") / "real_send_result.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"\n[截图] 已保存: {screenshot_path.name}")

        print("\n[提示] 浏览器将保持打开60秒，请手动确认...")
        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
