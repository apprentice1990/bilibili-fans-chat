#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探测评论区实际结构
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
    print("\n[探测] 分析评论区结构...")

    options = Options()
    options.add_argument('--window-size=1400,900')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://www.bilibili.com")
        time.sleep(2)

        with open(msg_config.COOKIE_FILE, 'rb') as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass

        driver.refresh()
        time.sleep(2)

        # 访问视频
        bv_id = "BV1TRzZBuEg6"
        print(f"[访问] {bv_id}")
        driver.get(f"https://www.bilibili.com/video/{bv_id}")
        time.sleep(10)

        # 滚动到评论区
        driver.execute_script("window.scrollTo(0, 4000);")
        time.sleep(5)

        # 探测评论区
        print("\n[分析] 评论区结构...")
        print("="*60)

        info = driver.execute_script("""
            var result = {
                replyContainers: [],
                allUserLinks: [],
                commentItems: []
            };

            // 1. 查找评论容器
            var containers = document.querySelectorAll('[class*="comment"], [class*="reply"], [id*="comment"], [id*="reply"]');
            for (var i = 0; i < Math.min(containers.length, 20); i++) {
                var con = containers[i];
                var rect = con.getBoundingClientRect();
                result.replyContainers.push({
                    tag: con.tagName,
                    class: con.className ? con.className.substring(0, 100) : '',
                    id: con.id || '',
                    visible: rect.width > 0 && rect.height > 0,
                    width: rect.width,
                    height: rect.height,
                    childrenCount: con.children.length
                });
            }

            // 2. 查找所有space.bilibili.com链接
            var allLinks = document.querySelectorAll('a[href*="space.bilibili.com"]');
            for (var i = 0; i < Math.min(allLinks.length, 50); i++) {
                var link = allLinks[i];
                var href = link.getAttribute('href');
                var userId = null;
                if (href.indexOf('//space.bilibili.com/') !== -1) {
                    userId = href.split('//space.bilibili.com/')[1].split('/')[0].split('?')[0];
                }

                // 查找这个链接附近的评论内容
                var parent = link;
                var foundComment = false;
                var commentText = '';

                for (var level = 0; level < 5; level++) {
                    parent = parent.parentElement;
                    if (!parent) break;

                    var contentElem = parent.querySelector('[class*="content"], [class*="text"], [class*="con"]');
                    if (contentElem && contentElem !== link) {
                        commentText = contentElem.textContent.substring(0, 50);
                        foundComment = true;
                        break;
                    }
                }

                result.allUserLinks.push({
                    index: i,
                    userId: userId,
                    nickname: link.textContent.substring(0, 30),
                    hasNearbyComment: foundComment,
                    nearbyText: commentText,
                    parentClass: link.parentElement ? link.parentElement.className.substring(0, 80) : ''
                });
            }

            // 3. 统计信息
            result.stats = {
                totalContainers: containers.length,
                totalUserLinks: allLinks.length,
                bodyHTML: document.body.innerHTML.substring(0, 500)
            };

            return result;
        """)

        print(f"评论容器数量: {len(info.get('replyContainers', []))}")
        for con in info.get('replyContainers', [])[:10]:
            print(f"\n  - tag={con.get('tag')} class={con.get('class')[:60]}")
            print(f"    visible={con.get('visible')} size={con.get('width')}x{con.get('height')}")

        print(f"\n\n用户链接数量: {len(info.get('allUserLinks', []))}")
        print("\n前20个用户链接:")
        for link in info.get('allUserLinks', [])[:20]:
            print(f"  [{link.get('index')}] ID={link.get('userId')} {link.get('nickname')}")
            if link.get('hasNearbyComment'):
                print(f"        附近有评论: {link.get('nearbyText')}")

        print("\n" + "="*60)
        print("[提示] 浏览器保持打开120秒，请手动检查F12查看评论区")
        print("[提示] 特别注意评论区区域的DOM结构")

        time.sleep(120)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
