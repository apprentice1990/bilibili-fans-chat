#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面结构探测：找到真正的输入框
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
    print("页面结构探测")
    print("="*60)

    user_id = "331613"

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

        # 保存初始页面截图
        screenshot1 = Path("debug_screenshots") / "probe_01_initial.png"
        driver.save_screenshot(str(screenshot1))
        print(f"[截图] 初始页面: {screenshot1.name}")

        # 详细探测页面元素
        print("\n[探测] 页面元素...")

        page_info = driver.execute_script("""
            var result = {
                allInputs: [],
                allTextareas: [],
                allContentEditables: [],
                allDivs: [],
                iframes: [],
                modals: []
            };

            // 探测所有input
            var inputs = document.querySelectorAll('input');
            for (var i = 0; i < inputs.length; i++) {
                result.allInputs.push({
                    index: i,
                    type: inputs[i].type,
                    placeholder: inputs[i].placeholder || '',
                    className: inputs[i].className || '',
                    id: inputs[i].id || '',
                    name: inputs[i].name || '',
                    disabled: inputs[i].disabled,
                    visible: inputs[i].offsetWidth > 0 && inputs[i].offsetHeight > 0
                });
            }

            // 探测所有textarea
            var textareas = document.querySelectorAll('textarea');
            for (var i = 0; i < textareas.length; i++) {
                var rect = textareas[i].getBoundingClientRect();
                result.allTextareas.push({
                    index: i,
                    placeholder: textareas[i].placeholder || '',
                    className: textareas[i].className || '',
                    id: textareas[i].id || '',
                    value: textareas[i].value || '',
                    disabled: textareas[i].disabled,
                    visible: rect.width > 0 && rect.height > 0,
                    width: rect.width,
                    height: rect.height,
                    parentTag: textareas[i].parentElement ? textareas[i].parentElement.tagName : ''
                });
            }

            // 探测contenteditable
            var editables = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                result.allContentEditables.push({
                    index: i,
                    tagName: editables[i].tagName,
                    className: editables[i].className || '',
                    id: editables[i].id || '',
                    textContent: editables[i].textContent.substring(0, 50) || '',
                    visible: rect.width > 0 && rect.height > 0,
                    width: rect.width,
                    height: rect.height
                });
            }

            // 探测iframe
            var iframes = document.querySelectorAll('iframe');
            for (var i = 0; i < iframes.length; i++) {
                result.iframes.push({
                    index: i,
                    src: iframes[i].src || '',
                    id: iframes[i].id || '',
                    className: iframes[i].className || ''
                });
            }

            // 探测可能的模态框/对话框
            var dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [class*="popup"], [role="dialog"]');
            for (var i = 0; i < dialogs.length; i++) {
                result.modals.push({
                    index: i,
                    className: dialogs[i].className || '',
                    textContent: dialogs[i].textContent.substring(0, 100) || ''
                });
            }

            return result;
        """)

        print(f"\n发现元素:")
        print(f"  input元素: {len(page_info.get('allInputs', []))}")
        print(f"  textarea元素: {len(page_info.get('allTextareas', []))}")
        print(f"  contenteditable元素: {len(page_info.get('allContentEditables', []))}")
        print(f"  iframe: {len(page_info.get('iframes', []))}")
        print(f"  模态框: {len(page_info.get('modals', []))}")

        # 显示所有textarea
        if page_info.get('allTextareas'):
            print(f"\nTextarea详情:")
            for ta in page_info.get('allTextareas'):
                ph = ta.get('placeholder', '')[:50].encode('gbk', errors='ignore').decode('gbk')
                print(f"  [{ta.get('index')}] {ta.get('width')}x{ta.get('height')} visible={ta.get('visible')}")
                print(f"      placeholder='{ph}'")
                cls = ta.get('className', '')[:50].encode('gbk', errors='ignore').decode('gbk')
                print(f"      class='{cls}'")
                print(f"      parent={ta.get('parentTag')}")

        # 显示contenteditable（重要！）
        if page_info.get('allContentEditables'):
            print(f"\nContentEditable详情:")
            for ce in page_info.get('allContentEditables'):
                cls = ce.get('className', '')[:80].encode('gbk', errors='ignore').decode('gbk')
                text = ce.get('textContent', '')[:50].encode('gbk', errors='ignore').decode('gbk')
                print(f"  [{ce.get('index')}] {ce.get('tagName')} {ce.get('width')}x{ce.get('height')}")
                print(f"      class='{cls}'")
                print(f"      text='{text}'")

        # 显示模态框（可能遮挡）
        if page_info.get('modals'):
            print(f"\n模态框/对话框:")
            for modal in page_info.get('modals'):
                cls = modal.get('className', '')[:80].encode('gbk', errors='ignore').decode('gbk')
                text = modal.get('textContent', '')[:100].encode('gbk', errors='ignore').decode('gbk')
                print(f"  [{modal.get('index')}] class='{cls}'")
                print(f"      text='{text}'")

        # 尝试查找所有可见的可输入元素
        print(f"\n[尝试] 查找所有可能的消息输入区域...")
        candidates = driver.execute_script("""
            var candidates = [];

            // 查找底部固定区域（通常是输入框所在位置）
            var fixedElements = [];
            var allElements = document.querySelectorAll('*');

            for (var i = 0; i < allElements.length; i++) {
                var style = window.getComputedStyle(allElements[i]);
                var rect = allElements[i].getBoundingClientRect();

                // 查找底部固定的元素
                if (style.position === 'fixed' && rect.bottom > window.innerHeight - 200) {
                    fixedElements.push({
                        tag: allElements[i].tagName,
                        className: allElements[i].className,
                        rect: {top: rect.top, left: rect.left, width: rect.width, height: rect.height}
                    });
                }
            }

            return {fixedCount: fixedElements.length, fixedElements: fixedElements.slice(0, 10)};
        """)

        print(f"  底部固定元素: {candidates.get('fixedCount')}")
        for elem in candidates.get('fixedElements', []):
            print(f"    {elem.get('tag')} class='{elem.get('className')[:40]}' pos={elem.get('rect')}")

        # 尝试查找React/Vue实例（页面框架）
        print(f"\n[探测] 页面框架...")
        framework = driver.execute_script("""
            return {
                hasReact: typeof React !== 'undefined' || !!document.querySelector('[data-reactroot]'),
                hasVue: typeof Vue !== 'undefined' || !!document.querySelector('[data-v-]'),
                bodyClass: document.body.className,
                appRoot: document.querySelector('#app, #root, [data-v-]') ? 'found' : 'not found'
            };
        """)
        print(f"  React: {framework.get('hasReact')}")
        print(f"  Vue: {framework.get('hasVue')}")
        print(f"  body class: {framework.get('bodyClass')[:100]}")

        print(f"\n[提示] 浏览器将保持打开60秒，请手动检查页面...")
        print(f"[提示] 特别注意页面底部是否有输入框")

        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
