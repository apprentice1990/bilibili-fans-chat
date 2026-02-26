#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试视频页面结构
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
    print("\n[调试] 探测视频页面结构...")
    print("="*60)

    # 初始化浏览器
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
        driver.get("https://www.bilibili.com")
        time.sleep(2)

        with open(msg_config.COOKIE_FILE, 'rb') as f:
            cookies = pickle.load(f)

        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                continue

        driver.refresh()
        time.sleep(2)

        # 访问视频
        bv_id = "BV1TRzZBuEg6"
        print(f"\n[访问] {bv_id}")
        driver.get(f"https://www.bilibili.com/video/{bv_id}")
        time.sleep(8)  # 等待页面完全加载

        # 滚动到评论区
        driver.execute_script("window.scrollTo(0, 3000);")
        time.sleep(3)

        # 探测页面元素
        print("\n[探测] 页面元素...")
        print("="*60)

        info = driver.execute_script("""
            var result = {
                allDivs: 0,
                replyClasses: [],
                userLinks: [],
                iframes: [],
                hasShadowDOM: false
            };

            // 统计所有div
            result.allDivs = document.querySelectorAll('div').length;

            // 查找包含reply的class
            var allElements = document.querySelectorAll('*');
            for (var i = 0; i < allElements.length; i++) {
                var className = allElements[i].className || '';
                if (typeof className === 'string' && className.indexOf('reply') !== -1) {
                    if (result.replyClasses.indexOf(className) === -1) {
                        result.replyClasses.push(className);
                    }
                }

                // 查找用户链接
                if (allElements[i].tagName === 'A') {
                    var href = allElements[i].getAttribute('href') || '';
                    if (href.indexOf('space.bilibili.com') !== -1) {
                        result.userLinks.push({
                            href: href,
                            text: allElements[i].textContent.substring(0, 30),
                            class: allElements[i].className
                        });
                    }
                }
            }

            // 限制返回数量
            result.replyClasses = result.replyClasses.slice(0, 20);
            result.userLinks = result.userLinks.slice(0, 10);

            // 检查iframe
            var iframes = document.querySelectorAll('iframe');
            for (var i = 0; i < iframes.length; i++) {
                result.iframes.push({
                    src: iframes[i].src || 'no-src',
                    id: iframes[i].id || ''
                });
            }

            return result;
        """)

        print(f"页面总div数: {info.get('allDivs')}")
        print(f"\n包含'reply'的class ({len(info.get('replyClasses', []))} 个):")
        for cls in info.get('replyClasses', []):
            print(f"  - {cls[:100]}")

        print(f"\n用户链接 ({len(info.get('userLinks', []))} 个):")
        for link in info.get('userLinks', []):
            print(f"  - href={link.get('href')[:60]}")
            print(f"    text={link.get('text')}")
            print(f"    class={link.get('class')[:80]}")

        print(f"\nIframes ({len(info.get('iframes', []))} 个):")
        for iframe in info.get('iframes', []):
            print(f"  - src={iframe.get('src')}")

        print("\n[提示] 浏览器保持打开60秒，请手动检查页面...")
        print("[提示] 按F12打开开发者工具查看评论区域")

        time.sleep(60)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
