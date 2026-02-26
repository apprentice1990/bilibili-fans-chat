#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单用户逐步测试：测试私信发送的每一步
"""

import json
import pickle
import time
import random
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

def load_users_from_json(json_file):
    """从JSON文件加载用户列表"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['users']

def send_with_steps(driver, wait, user_id, nickname, message):
    """逐步测试发送流程"""
    url = f"https://space.bilibili.com/{user_id}"

    try:
        # 步骤1: 访问用户主页
        print(f"\n[步骤1] 访问用户主页: {url}")
        driver.get(url)
        time.sleep(5)
        print(f"  [OK] 页面加载成功")

        # 步骤2: 查找"发消息"按钮
        print(f"\n[步骤2] 查找'发消息'按钮...")
        try:
            msg_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '发消息')]"))
            )
            print(f"  [OK] 找到按钮")
        except Exception as e:
            print(f"  [SKIP] 未找到按钮: {str(e)[:100]}")
            return {"status": "skip", "reason": "用户限制私信"}

        # 步骤3: 点击打开对话框
        print(f"\n[步骤3] 点击'发消息'按钮...")
        try:
            msg_btn.click()
            time.sleep(3)
            print(f"  [OK] 点击成功")

            # 保存截图
            screenshot_path = Path("debug_screenshots") / f"after_click_{user_id}.png"
            driver.save_screenshot(str(screenshot_path))
            print(f"  [截图] 已保存: {screenshot_path.name}")

            # 检查iframe
            iframe_info = driver.execute_script("""
                var iframes = document.querySelectorAll('iframe');
                var result = {
                    count: iframes.length,
                    iframes: []
                };

                for (var i = 0; i < iframes.length; i++) {
                    result.iframes.push({
                        src: iframes[i].src || '',
                        id: iframes[i].id || '',
                        className: iframes[i].className || '',
                        name: iframes[i].name || ''
                    });
                }

                return result;
            """)

            print(f"  [调试] iframe数量: {iframe_info.get('count')}")
            if iframe_info.get('iframes'):
                print(f"  [调试] 找到的iframe:")
                for idx, iframe in enumerate(iframe_info.get('iframes', [])):
                    src = iframe.get('src', '')[:60]
                    print(f"    {idx+1}. src={src}")

            # 获取对话框HTML
            dialog_html = driver.execute_script("""
                // 查找可能的对话框容器
                var dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [class*="popup"]');
                if (dialogs.length > 0) {
                    return dialogs[0].outerHTML.substring(0, 1000);
                }

                // 查找所有固定定位的元素（可能是对话框）
                var fixed = document.querySelectorAll('[style*="position: fixed"]');
                if (fixed.length > 0) {
                    return fixed[0].outerHTML.substring(0, 1000);
                }

                return null;
            """)

            if dialog_html:
                print(f"  [调试] 对话框HTML片段:")
                print(f"    {dialog_html[:300]}...")

        except Exception as e:
            print(f"  [FAIL] 点击失败: {str(e)[:200]}")
            return {"status": "failed", "reason": f"点击失败: {str(e)[:100]}"}

        # 步骤4: 查找消息输入框（可能在iframe中）
        print(f"\n[步骤4] 查找消息输入框...")
        try:
            # 等待对话框完全加载
            time.sleep(3)

            # 使用JavaScript查找message iframe
            iframe_result = driver.execute_script("""
                var iframes = document.querySelectorAll('iframe');
                for (var i = 0; i < iframes.length; i++) {
                    var src = iframes[i].src || '';
                    if (src.indexOf('message.bilibili.com') !== -1) {
                        return {found: true, index: i};
                    }
                }
                return {found: false};
            """)

            # 总是先尝试第二个iframe（iframe.html通常是对话框）
            in_iframe = False

            # 获取所有iframe信息
            all_iframes = driver.execute_script("""
                var iframes = document.querySelectorAll('iframe');
                var result = [];
                for (var i = 0; i < iframes.length; i++) {
                    result.push({
                        index: i,
                        src: iframes[i].src || ''
                    });
                }
                return result;
            """)

            print(f"  [调试] 所有iframe:")
            for idx, ifr in enumerate(all_iframes):
                src = ifr.get('src', '')[:60]
                print(f"    {idx}: {src}")

            # 尝试第二个iframe（通常是消息对话框）
            if len(all_iframes) >= 2:
                print(f"  [调试] 尝试切换到第二个iframe (iframe.html)...")
                try:
                    driver.switch_to.frame(1)
                    in_iframe = True
                    time.sleep(2)
                    print(f"  [调试] 已切换到第二个iframe")

                    # 获取iframe内容
                    iframe_content = driver.execute_script("""
                        return document.body.innerHTML.substring(0, 2000);
                    """)
                    print(f"  [调试] iframe内容长度: {len(iframe_content) if iframe_content else 0}")
                    if iframe_content and len(iframe_content) > 0:
                        print(f"  [调试] iframe内容片段: {iframe_content[:200]}...")
                except Exception as e:
                    print(f"  [调试] 切换失败: {str(e)[:100]}")
            else:
                print(f"  [调试] iframe数量不足")

            # 使用JavaScript查找并分析输入框
            debug_info = driver.execute_script("""
                var result = {
                    textareaCount: 0,
                    contentEditableCount: 0,
                    inputCount: 0,
                    inputs: [],
                    found: false
                };

                // 查找所有textarea
                var textareas = document.querySelectorAll('textarea');
                result.textareaCount = textareas.length;
                if (textareas.length > 0) {
                    result.found = true;
                    result.type = 'textarea';
                    result.placeholder = textareas[0].placeholder || '';
                    result.tagName = 'textarea';
                    return result;
                }

                // 查找可能的内容editable div
                var editables = document.querySelectorAll('[contenteditable="true"]');
                result.contentEditableCount = editables.length;
                if (editables.length > 0) {
                    result.found = true;
                    result.type = 'contenteditable';
                    result.tagName = editables[0].tagName;
                    return result;
                }

                // 查找所有input
                var inputs = document.querySelectorAll('input');
                result.inputCount = inputs.length;

                // 收集前5个input的信息
                for (var i = 0; i < Math.min(5, inputs.length); i++) {
                    result.inputs.push({
                        type: inputs[i].type || 'text',
                        placeholder: inputs[i].placeholder || '',
                        className: inputs[i].className || '',
                        id: inputs[i].id || ''
                    });
                }

                // 尝试找到合适的input（用于消息输入）
                for (var i = 0; i < inputs.length; i++) {
                    // 跳过hidden、submit、button类型
                    if (inputs[i].type === 'hidden' || inputs[i].type === 'submit' || inputs[i].type === 'button') {
                        continue;
                    }
                    // 查找有placeholder或class包含"input"、"message"、"content"的
                    var ph = inputs[i].placeholder || '';
                    var cls = inputs[i].className || '';
                    if (ph || cls.indexOf('input') !== -1 || cls.indexOf('message') !== -1 || cls.indexOf('content') !== -1) {
                        result.found = true;
                        result.type = 'input';
                        result.tagName = 'input';
                        result.inputIndex = i;
                        return result;
                    }
                }

                // 如果没找到合适的，使用第一个非hidden的input
                for (var i = 0; i < inputs.length; i++) {
                    if (inputs[i].type !== 'hidden' && inputs[i].type !== 'submit' && inputs[i].type !== 'button') {
                        result.found = true;
                        result.type = 'input';
                        result.tagName = 'input';
                        result.inputIndex = i;
                        return result;
                    }
                }

                return result;
            """)

            print(f"  [调试] (iframe中) textarea: {debug_info.get('textareaCount')}, "
                  f"contentEditable: {debug_info.get('contentEditableCount')}, "
                  f"input: {debug_info.get('inputCount')}")

            # 打印找到的input信息
            if debug_info.get('inputs'):
                print(f"  [调试] 找到的input元素:")
                for inp in debug_info.get('inputs', []):
                    print(f"    - type={inp.get('type')}, placeholder={inp.get('placeholder')}, "
                          f"class={inp.get('className')[:30] if inp.get('className') else ''}")

            if not debug_info.get('found'):
                # 切换回主页面
                driver.switch_to.default_content()
                print(f"  [FAIL] 未找到输入框")
                return {"status": "failed", "reason": "未找到输入框"}

            print(f"  [OK] 找到输入框 (类型: {debug_info.get('type')}, 标签: {debug_info.get('tagName')})")

            # 保存找到的元素信息供后续使用
            input_info = debug_info
            in_iframe = iframe_found
        except Exception as e:
            print(f"  [FAIL] 查找失败: {str(e)[:200]}")
            return {"status": "failed", "reason": f"查找失败: {str(e)[:100]}"}

        # 步骤5: 填写消息（使用JavaScript）
        print(f"\n[步骤5] 使用JavaScript填写消息...")
        try:
            fill_result = driver.execute_script("""
                var message = arguments[0];

                // 尝试找到textarea
                var textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.value = message;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    return {success: true, type: 'textarea'};
                }

                // 尝试找到contenteditable div
                var editable = document.querySelector('[contenteditable="true"]');
                if (editable) {
                    editable.textContent = message;
                    editable.dispatchEvent(new Event('input', { bubbles: true }));
                    return {success: true, type: 'contenteditable'};
                }

                return {success: false, error: '未找到输入元素'};
            """, message)

            if not fill_result.get('success'):
                print(f"  [FAIL] {fill_result.get('error', '未知错误')}")
                return {"status": "failed", "reason": fill_result.get('error', '未知错误')}

            print(f"  [OK] 消息填写成功 (类型: {fill_result.get('type')})")
            time.sleep(1)
        except Exception as e:
            print(f"  [FAIL] 填写失败: {str(e)[:200]}")
            return {"status": "failed", "reason": f"填写失败: {str(e)[:100]}"}

        # 步骤6-7: 查找并点击发送按钮（使用JavaScript）
        print(f"\n[步骤6] 使用JavaScript查找并点击发送按钮...")
        try:
            send_result = driver.execute_script("""
                // 查找包含"发送"文本的按钮
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    if (buttons[i].textContent.indexOf('发送') !== -1) {
                        buttons[i].click();
                        return {success: true, text: buttons[i].textContent};
                    }
                }

                // 查找带有发送类名的按钮
                var sendBtn = document.querySelector('.send-btn, [class*="send"]');
                if (sendBtn) {
                    sendBtn.click();
                    return {success: true, text: sendBtn.textContent};
                }

                return {success: false, error: '未找到发送按钮'};
            """)

            if not send_result.get('success'):
                print(f"  [FAIL] {send_result.get('error', '未知错误')}")
                return {"status": "failed", "reason": send_result.get('error', '未知错误')}

            print(f"  [OK] 点击发送成功 (按钮: {send_result.get('text', '')})")
            time.sleep(3)
        except Exception as e:
            print(f"  [FAIL] 发送失败: {str(e)[:200]}")
            return {"status": "failed", "reason": f"发送失败: {str(e)[:100]}"}

        print(f"\n{'='*60}")
        print(f"[SUCCESS] 私信发送成功！")
        print(f"{'='*60}")

        return {"status": "success"}

    except Exception as e:
        print(f"\n[FAIL] 异常: {str(e)[:300]}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "reason": str(e)[:200]}

def main():
    print("\n" + "="*60)
    print("单用户逐步测试")
    print("="*60)

    # 加载用户列表
    json_file = "data/users/BV1TRzZBuEg6_20260225_163222.json"

    if not Path(json_file).exists():
        print(f"[错误] 文件不存在: {json_file}")
        return

    users = load_users_from_json(json_file)
    print(f"[OK] 已加载 {len(users)} 位用户")

    # 测试用户4（我们知道他可以接收私信）
    user = users[3]  # 用户4
    print(f"\n测试用户:")
    print(f"  昵称: {user['nickname']}")
    print(f"  ID: {user['user_id']}")
    print(f"  评论: {user['comment'][:50]}...")

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

    # 确认
    print(f"\n[提示] 将逐步测试发送流程，每步都会显示结果")
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("[自动] 自动确认模式")
    else:
        confirm = input("\n确认开始？(yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("[取消] 已取消")
            return

    # 初始化浏览器（使用稳定选项）
    print("\n[浏览器] 初始化中...")
    options = Options()
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--hide-scrollbars')
    options.add_argument('--metrics-recording-only')
    options.add_argument('--mute-audio')
    options.add_argument('--no-first-run')
    options.add_argument('--safebrowsing-disable-auto-update')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--log-level=3')
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

        # 发送消息
        result = send_with_steps(driver, wait, user['user_id'], user['nickname'], message)

        # 显示结果
        print(f"\n{'='*60}")
        print("最终结果")
        print(f"{'='*60}")
        print(f"状态: {result['status']}")
        if 'reason' in result:
            print(f"原因: {result['reason']}")

        # 等待查看结果
        print("\n[提示] 浏览器将保持打开60秒，请查看结果...")
        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
