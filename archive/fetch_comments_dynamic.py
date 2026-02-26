#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版爬虫 - 处理动态加载的评论区
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

def fetch_comments_dynamic(bv_id):
    """获取动态加载的评论"""
    print(f"\n[爬虫] 获取视频 {bv_id} 的评论用户")
    print(f"[模式] 等待动态加载并持续滚动\n")

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

        # 等待页面加载
        print("[等待] 页面初始加载...")
        time.sleep(8)

        # 滚动到评论区
        print("[定位] 滚动到评论区...")
        driver.execute_script("window.scrollTo(0, 3500);")
        time.sleep(5)

        # 等待评论区出现（尝试多种选择器）
        comment_loaded = False
        for selector in [
            '#comment',
            '.video-page-game-comment-card',
            '#reply_box',
            '.reply-box',
            '[class*="comment"]'
        ]:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    print(f"[找到] 评论区元素: {selector}")
                    comment_loaded = True
                    break
            except:
                continue

        if not comment_loaded:
            print("[提示] 未找到明显的评论区容器，尝试直接提取...")

        # 收集用户
        users = []
        seen = set()
        last_count = 0
        no_new_count = 0
        scroll_num = 0
        max_scrolls = 50

        print("\n[开始] 滚动并提取评论...")
        print("="*60)

        while scroll_num < max_scrolls and no_new_count < 10:
            # 方法1: 使用JavaScript从DOM中提取
            page_users = driver.execute_script("""
                var users = [];
                var seen = arguments[0];

                // 查找所有包含用户链接的元素
                var allElements = document.querySelectorAll('*');

                for (var i = 0; i < allElements.length; i++) {
                    var elem = allElements[i];

                    // 查找用户链接
                    var links = elem.querySelectorAll ? elem.querySelectorAll('a[href*="space.bilibili.com"]') : [];

                    if (links.length === 0) continue;

                    for (var j = 0; j < links.length; j++) {
                        var link = links[j];
                        var href = link.getAttribute('href');

                        if (!href || href.indexOf('//space.bilibili.com/') === -1) continue;

                        var userId = href.split('//space.bilibili.com/')[1].split('/')[0].split('?')[0];

                        if (!userId || seen[userId]) continue;

                        var nickname = link.textContent.trim();
                        if (!nickname || nickname.length > 50) continue;

                        // 查找附近的文本作为评论内容
                        var parent = link;
                        var commentText = '';

                        for (var level = 0; level < 8; level++) {
                            if (!parent.parentElement) break;
                            parent = parent.parentElement;

                            // 在父元素中查找文本
                            var textNodes = [];
                            var walker = document.createTreeWalker(
                                parent,
                                NodeFilter.SHOW_TEXT,
                                null,
                                false
                            );

                            var node;
                            while (node = walker.nextNode()) {
                                var text = node.textContent.trim();
                                if (text && text.length > 5 && text.length < 200 &&
                                    text.indexOf(nickname) === -1 &&
                                    text.indexOf('回复') === -1) {
                                    textNodes.push(text);
                                    if (textNodes.length >= 3) break;
                                }
                            }

                            if (textNodes.length > 0) {
                                commentText = textNodes[0];
                                break;
                            }
                        }

                        users.push({
                            user_id: String(userId),
                            nickname: nickname,
                            comment: commentText.substring(0, 100)
                        });
                    }
                }

                return users;
            """, {str(uid): True for uid in seen})

            # 添加新用户
            new_count = 0
            for user in page_users:
                if user['user_id'] not in seen:
                    seen.add(user['user_id'])
                    users.append(user)
                    new_count += 1

            current_total = len(users)

            if new_count > 0:
                print(f"[进度] 滚动#{scroll_num+1}: +{new_count} 位，总计 {current_total} 位")
                last_count = current_total
                no_new_count = 0
            else:
                no_new_count += 1
                if no_new_count <= 3:
                    print(f"[提示] 滚动#{scroll_num+1}: 无新用户 ({no_new_count}/10)")

            # 滚动页面
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # 尝试点击"加载更多"类型按钮
            try:
                load_more = driver.execute_script("""
                    var buttons = document.querySelectorAll('button, a, div[role="button"]');
                    for (var i = 0; i < buttons.length; i++) {
                        var text = buttons[i].textContent || '';
                        if ((text.indexOf('更多') !== -1 ||
                             text.indexOf('展开') !== -1 ||
                             text.indexOf('加载') !== -1 ||
                             text.indexOf('下一页') !== -1) &&
                            buttons[i].offsetParent !== null) {
                            return buttons[i];
                        }
                    }
                    return null;
                """)

                if load_more:
                    print("  [点击] 加载更多按钮")
                    driver.execute_script("arguments[0].click();", load_more)
                    time.sleep(3)
            except:
                pass

            # 回到评论区区域
            driver.execute_script("window.scrollTo(0, Math.max(4000, document.body.scrollHeight - 1000));")
            time.sleep(random.uniform(1.5, 3))

            scroll_num += 1

            # 检查页面是否有新内容
            new_scroll_height = driver.execute_script("return document.body.scrollHeight")
            if new_scroll_height == scroll_height and no_new_count > 3:
                print(f"[提示] 页面高度未变化，可能到底部了")
                break

        print("="*60)
        print(f"\n[完成] 滚动{scroll_num}次，获取 {len(users)} 位用户")

        # 保存
        if users:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{bv_id}_dynamic_{timestamp}.json"
            filepath = Path(msg_config.USERS_DIR) / filename

            data = {
                "bv_id": bv_id,
                "fetched_at": datetime.now().isoformat(),
                "total_users": len(users),
                "users": users
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[保存] {filepath}")

            # 显示用户
            print(f"\n[预览] 所有用户:")
            for i, user in enumerate(users, 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
                if user.get('comment'):
                    print(f"   评论: {user['comment'][:50]}")

        return users

    finally:
        print("\n[完成] 关闭浏览器")
        time.sleep(3)
        driver.quit()

def main():
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    users = fetch_comments_dynamic(bv_id)
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
