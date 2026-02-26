#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激进版爬虫 - 持续滚动和点击以加载所有评论
"""

import pickle
import time
import json
import random
from pathlib import Path
from datetime import datetime
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

def fetch_comments_aggressive(bv_id, max_users=500):
    """激进式获取评论 - 持续滚动和点击"""
    print(f"\n[爬虫] 激进模式获取评论")
    print(f"[视频] {bv_id}")
    print(f"[目标] 最多获取 {max_users} 位用户\n")

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
    wait = WebDriverWait(driver, 10)

    try:
        # 加载cookies
        print("[Cookies] 加载中...")
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
        video_url = f"https://www.bilibili.com/video/{bv_id}"
        print(f"[访问] {video_url}\n")
        driver.get(video_url)
        time.sleep(8)

        # 滚动到评论区
        print("[定位] 滚动到评论区...")
        driver.execute_script("window.scrollTo(0, 3000);")
        time.sleep(5)

        users = {}
        seen = set()

        print("[开始] 激进滚动和点击...")
        print("="*60)

        last_user_count = 0
        no_new_count = 0
        scroll_num = 0
        max_scrolls = 200

        while scroll_num < max_scrolls and len(users) < max_users:
            # 方法1: 点击所有可能的"更多"按钮
            try:
                # 查找包含"更多"、"查看更多"、"加载更多"等文字的元素
                more_buttons = driver.execute_script("""
                    var result = [];
                    var allElements = document.querySelectorAll('*');

                    for (var i = 0; i < allElements.length; i++) {
                        var elem = allElements[i];
                        var text = elem.textContent || '';
                        var trimmed = text.trim();

                        // 检查是否包含关键词
                        if (trimmed.indexOf('更多') !== -1 ||
                            trimmed.indexOf('展开') !== -1 ||
                            trimmed.indexOf('查看') !== -1 ||
                            trimmed.indexOf('评论') !== -1) {

                            // 检查是否可见
                            var rect = elem.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                result.push({
                                    tag: elem.tagName,
                                    text: trimmed.substring(0, 30),
                                    clickable: elem.tagName === 'BUTTON' ||
                                              elem.tagName === 'A' ||
                                              elem.onclick !== null
                                });
                            }
                        }
                    }

                    return result;
                """)

                if more_buttons and scroll_num % 5 == 0:
                    print(f"\n[发现] {len(more_buttons)} 个可能的按钮")
                    for btn in more_buttons[:3]:
                        print(f"  - {btn['tag']}: {btn['text']} (可点击: {btn['clickable']})")

            except Exception as e:
                pass

            # 方法2: 尝试点击"查看更多评论"
            try:
                # 使用XPath查找
                more_comment_btns = driver.find_elements(By.XPATH,
                    "//*[contains(text(), '查看更多评论') or contains(text(), '更多评论') or contains(text(), '全部评论')]")
                for btn in more_comment_btns:
                    if btn.is_displayed():
                        print("  [点击] 查看更多评论按钮")
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(3)
                        break
            except:
                pass

            # 方法3: 滚动到评论区域底部
            try:
                # 先滚动到页面底部
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1.5, 3))

                # 再滚动到评论区位置
                driver.execute_script("window.scrollTo(0, Math.max(3000, document.body.scrollHeight - 500));")
                time.sleep(random.uniform(1, 2))
            except:
                pass

            # 方法4: 使用JavaScript提取当前页面上的用户
            page_users = driver.execute_script("""
                var users = [];
                var seen = arguments[0];

                // 查找所有评论相关的元素
                var commentSelectors = [
                    '.reply-item',
                    '.reply-wrap',
                    '[class*="reply-item"]',
                    '[class*="comment-item"]',
                    '[class*="reply-wrap"]'
                ];

                var allItems = [];
                for (var sel of commentSelectors) {
                    var items = document.querySelectorAll(sel);
                    for (var item of items) {
                        allItems.push(item);
                    }
                }

                // 如果没找到，尝试查找包含用户链接的元素
                if (allItems.length === 0) {
                    var userLinks = document.querySelectorAll('a[href*="space.bilibili.com"]');
                    for (var link of userLinks) {
                        allItems.push(link.closest('div'));
                    }
                }

                for (var item of allItems) {
                    if (!item) continue;

                    // 查找用户链接
                    var userLink = item.querySelector('a[href*="space.bilibili.com"]');
                    if (!userLink) continue;

                    var href = userLink.getAttribute('href');
                    if (!href || href.indexOf('//space.bilibili.com/') === -1) continue;

                    var userId = href.split('//space.bilibili.com/')[1].split('/')[0].split('?')[0];
                    if (!userId || seen[userId]) continue;

                    var nickname = userLink.textContent.trim();
                    if (!nickname || nickname.length > 50) continue;

                    // 查找评论内容
                    var commentText = '';
                    var contentElem = item.querySelector('[class*="content"], [class*="text"], [class*="message"]');
                    if (contentElem) {
                        commentText = contentElem.textContent.trim().substring(0, 100);
                    }

                    users.push({
                        user_id: String(userId),
                        nickname: nickname,
                        comment: commentText
                    });
                }

                return users;
            """, {str(uid): True for uid in seen})

            # 添加新用户
            new_count = 0
            for user in page_users:
                if user['user_id'] not in seen:
                    seen.add(user['user_id'])
                    users[user['user_id']] = user
                    new_count += 1
                    print(f"  [{len(users)}] {user['nickname']}")

            current_total = len(users)

            if new_count > 0:
                print(f"[进度] 滚动#{scroll_num+1}: +{new_count} 位，总计 {current_total} 位")
                last_user_count = current_total
                no_new_count = 0
            else:
                no_new_count += 1
                if no_new_count <= 3:
                    print(f"[提示] 滚动#{scroll_num+1}: 无新用户 ({no_new_count}/20)")

            # 如果连续20次没有新用户，可能真的到底了
            if no_new_count >= 20:
                print(f"\n[提示] 连续{no_new_count}次无新用户，可能已加载全部评论")
                break

            scroll_num += 1

        print("="*60)
        print(f"\n[完成] 滚动{scroll_num}次，获取 {len(users)} 位用户")

        # 保存
        if users:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{bv_id}_aggressive_{timestamp}.json"
            filepath = Path(msg_config.USERS_DIR) / filename

            user_list = list(users.values())
            data = {
                "bv_id": bv_id,
                "fetched_at": datetime.now().isoformat(),
                "total_users": len(user_list),
                "users": user_list
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[保存] {filepath}")

            # 显示所有用户
            print(f"\n[预览] 所有用户:")
            for i, user in enumerate(user_list, 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
                if user.get('comment'):
                    comment = user['comment'][:40]
                    print(f"   评论: {comment}")

        return list(users.values())

    finally:
        print("\n[完成] 关闭浏览器")
        time.sleep(3)
        driver.quit()

def main():
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    max_users = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    users = fetch_comments_aggressive(bv_id, max_users)
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
