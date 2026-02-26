#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试多个用户，找到可以发送的
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

def check_user(driver, user_id, nickname):
    """检查用户是否可以发送私信"""
    try:
        msg_url = f"https://message.bilibili.com/#/whisper/mid{user_id}"
        driver.get(msg_url)
        time.sleep(3)

        # 检查页面状态
        result = driver.execute_script("""
            // 检查是否有"无法发起私信"的提示
            var allElements = document.querySelectorAll('*');
            var restrictionMsg = '';
            for (var i = 0; i < allElements.length; i++) {
                var text = allElements[i].textContent || '';
                if (text.indexOf('无法发起私信') !== -1 ||
                    text.indexOf('不是好友') !== -1 ||
                    text.indexOf('限制') !== -1) {
                    restrictionMsg = text.substring(0, 50);
                    break;
                }
            }

            // 检查是否有发送按钮
            var buttons = document.querySelectorAll('button');
            var sendBtn = false;
            for (var i = 0; i < buttons.length; i++) {
                if (!buttons[i].disabled && buttons[i].textContent.indexOf('发送') !== -1) {
                    sendBtn = true;
                    break;
                }
            }

            // 检查textarea是否可用
            var textarea = document.querySelector('textarea');
            var textareaUsable = textarea && !textarea.disabled;

            return {
                restriction: restrictionMsg,
                hasSendButton: sendBtn,
                textareaUsable: textareaUsable,
                canSend: !restrictionMsg && (sendBtn || textareaUsable)
            };
        """)

        return result

    except Exception as e:
        return {"error": str(e)[:100]}

def main():
    print("\n" + "="*60)
    print("快速测试多个用户")
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

    # 测试用户5-10
    start_index = 4  # 用户5
    end_index = 10

    print(f"\n测试用户 {start_index+1}-{end_index}:")

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

        # 逐个测试
        can_send_users = []

        for i in range(start_index, min(end_index, len(users))):
            user = users[i]
            print(f"\n{i+1}. {user['nickname']} (ID: {user['user_id']})")

            result = check_user(driver, user['user_id'], user['nickname'])

            if 'error' in result:
                print(f"   [错误] {result['error']}")
            elif result.get('canSend'):
                print(f"   [OK] 可以发送私信！")
                can_send_users.append((i, user))
            else:
                reason = result.get('restriction', '未知原因')
                print(f"   [SKIP] {reason}")

            # 用户间延迟
            time.sleep(2)

        # 显示结果
        print(f"\n{'='*60}")
        print(f"测试完成")
        print(f"{'='*60}")
        print(f"可发送用户: {len(can_send_users)}")

        if can_send_users:
            print(f"\n可以发送私信的用户:")
            for idx, user in can_send_users:
                print(f"  {idx+1}. {user['nickname']} (ID: {user['user_id']})")
        else:
            print(f"\n[提示] 所测试用户都限制私信")

        # 如果找到可发送的用户，尝试发送给第一个
        if can_send_users:
            first_user_idx, first_user = can_send_users[0]

            print(f"\n[尝试] 向 {first_user['nickname']} 发送测试消息...")

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

            # 导航到该用户的私信页面
            msg_url = f"https://message.bilibili.com/#/whisper/mid{first_user['user_id']}"
            driver.get(msg_url)
            time.sleep(3)

            # 尝试发送
            send_result = driver.execute_script("""
                var message = arguments[0];
                var textareas = document.querySelectorAll('textarea');

                if (textareas.length === 0) return {success: false, error: '无输入框'};

                var textarea = textareas[textareas.length - 1];
                textarea.focus();
                textarea.value = message;
                textarea.dispatchEvent(new Event('input', {bubbles: true}));

                // 尝试Enter
                var enterEvent = new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
                });
                textarea.dispatchEvent(enterEvent);

                return {success: true};
            """, message)

            if send_result.get('success'):
                print(f"  [OK] 已尝试发送")
                time.sleep(2)

                # 检查是否清空
                check = driver.execute_script("""
                    var t = document.querySelector('textarea');
                    return t ? t.value.length : 0;
                """)
                print(f"  [检查] 输入框内容长度: {check}")
                if check == 0:
                    print(f"  [成功] 消息已发送！")
                else:
                    print(f"  [提示] 输入框未清空，可能未发送")

        print(f"\n[提示] 浏览器将保持打开30秒...")
        time.sleep(30)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
