#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终可工作的发送脚本
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

def activate_and_send(driver, user_id, message):
    """激活textarea并发送消息"""
    try:
        # 导航到私信页面
        msg_url = f"https://message.bilibili.com/#/whisper/mid{user_id}"
        driver.get(msg_url)
        time.sleep(5)

        # 激活并输入
        result = driver.execute_script("""
            var message = arguments[0];

            // 1. 找到textarea
            var textareas = document.querySelectorAll('textarea');
            if (textareas.length === 0) return {success: false, error: '未找到textarea'};

            var textarea = textareas[textareas.length - 1];

            // 2. 激活textarea（关键步骤）
            // 确保父元素可见
            var parent = textarea.parentElement;
            while (parent && parent.tagName !== 'BODY') {
                parent.style.display = '';
                parent.style.visibility = 'visible';
                parent.style.opacity = '1';
                parent = parent.parentElement;
            }

            // 设置textarea样式
            textarea.style.display = 'block';
            textarea.style.visibility = 'visible';
            textarea.style.opacity = '1';

            // 滚动到视图
            textarea.scrollIntoView({block: 'center', inline: 'center'});

            // 3. 聚焦并输入
            textarea.focus();
            textarea.click();

            // 等待一下
            textarea.value = '';

            // 4. 输入消息
            textarea.value = message;

            // 5. 触发所有必要的事件
            var events = ['focus', 'input', 'change', 'keyup'];
            events.forEach(function(type) {
                var event = new Event(type, {bubbles: true, cancelable: true});
                textarea.dispatchEvent(event);
            });

            // 6. 等待一下让UI更新
            // 7. 查找并点击发送按钮
            setTimeout(function() {
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    var text = buttons[i].textContent.trim();
                    // 查找包含"发送"且未禁用的按钮
                    if (text.indexOf('发送') !== -1 && !buttons[i].disabled) {
                        buttons[i].click();
                        return;
                    }
                }

                // 如果没找到按钮，尝试Ctrl+Enter
                var ctrlEnterEvent = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    ctrlKey: true,
                    cancelable: true
                });
                textarea.dispatchEvent(ctrlEnterEvent);
            }, 500);

            return {
                success: true,
                messageLength: message.length,
                activated: true
            };
        """, message)

        # 等待UI更新（setTimeout的时间）
        time.sleep(1)

        # 步骤2: 单独执行发送逻辑（不使用setTimeout）
        send_result = driver.execute_script("""
            // 查找所有按钮
            var buttons = document.querySelectorAll('button');

            // 查找并发送按钮
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.trim();
                // 查找包含"发送"且未禁用的按钮
                if (text.indexOf('发送') !== -1 && !buttons[i].disabled) {
                    buttons[i].click();
                    return {success: true, method: 'button', text: text};
                }
            }

            // 如果没找到发送按钮，尝试所有非禁用按钮
            for (var i = 0; i < buttons.length; i++) {
                if (!buttons[i].disabled && buttons[i].textContent.trim()) {
                    buttons[i].click();
                    return {success: true, method: 'available-button', text: buttons[i].textContent.trim()};
                }
            }

            // 最后尝试: Ctrl+Enter
            var textarea = document.querySelector('textarea');
            if (textarea) {
                var ctrlEnterEvent = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    ctrlKey: true,
                    cancelable: true
                });
                textarea.dispatchEvent(ctrlEnterEvent);

                // 也尝试普通Enter
                var enterEvent = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    cancelable: true
                });
                textarea.dispatchEvent(enterEvent);

                return {success: true, method: 'keyboard', keys: 'Enter/Ctrl+Enter'};
            }

            return {success: false, error: '无发送方法', buttonsCount: buttons.length};
        """)

        print(f"    [调试] 发送结果: {send_result}")

        # 等待发送完成
        time.sleep(3)

        # 检查结果
        check = driver.execute_script("""
            var textarea = document.querySelector('textarea');
            if (!textarea) return {error: 'textarea不存在'};

            return {
                valueLength: textarea.value.length,
                value: textarea.value.substring(0, 100),
                isEmpty: textarea.value.length === 0,
                focused: document.activeElement === textarea
            };
        """)

        if 'error' in check:
            return {"success": False, "error": check['error']}

        success = check.get('isEmpty', False)

        return {
            "success": success,
            "result": result,
            "check": check,
            "debug": f"输入框长度: {check.get('valueLength')}, 聚焦: {check.get('focused')}"
        }

    except Exception as e:
        import traceback
        return {"success": False, "error": f"{str(e)[:200]} | {traceback.format_exc()[:500]}"}

def main():
    print("\n" + "="*60)
    print("最终发送脚本（已验证可用）")
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

    print(f"\n消息内容:")
    print("-"*60)
    print(message)
    print("-"*60)

    # 测试用户5-7
    test_users = [4, 5, 6]  # 索引4-6对应用户5-7

    print(f"\n测试用户:")
    for idx in test_users:
        if idx < len(users):
            user = users[idx]
            print(f"  {idx+1}. {user['nickname']} (ID: {user['user_id']})")

    print(f"\n[提示] 将依次测试，发送成功后停止")

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
        stats = {"success": 0, "failed": 0}

        for idx in test_users:
            if idx >= len(users):
                break

            user = users[idx]
            print(f"\n{'='*60}")
            print(f"测试用户 {idx+1}: {user['nickname']}")
            print(f"{'='*60}")

            result = activate_and_send(driver, user['user_id'], message)

            if result.get('success'):
                stats['success'] += 1
                print(f"  [OK] 发送成功！")
                print(f"\n{'='*60}")
                print(f"[SUCCESS] 已成功向 {user['nickname']} 发送私信！")
                print(f"{'='*60}")
                break  # 发送成功，停止测试
            else:
                stats['failed'] += 1
                error = result.get('error', '未知错误')
                debug = result.get('debug', '')
                print(f"  [FAIL] 发送失败: {error}")
                if debug:
                    print(f"  [调试] {debug}")

            # 用户间延迟
            if idx < test_users[-1]:
                print(f"\n[等待] 5秒后继续...")
                time.sleep(5)

        # 统计
        print(f"\n{'='*60}")
        print("测试完成")
        print(f"{'='*60}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failed']}")

        # 保存截图
        screenshot_path = Path("debug_screenshots") / "final_send_result.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"\n[截图] 已保存: {screenshot_path.name}")

        print("\n[提示] 浏览器将保持打开30秒，请查看结果...")
        time.sleep(30)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
