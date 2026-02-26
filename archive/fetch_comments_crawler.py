#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium爬虫获取评论用户
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
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def fetch_comments_crawler(bv_id):
    """使用Selenium爬虫获取评论用户"""
    print(f"\n[爬虫] 获取视频 {bv_id} 的评论用户...")
    print(f"[提示] 将滚动页面加载所有评论\n")

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
        print("[Cookies] 加载中...")
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

        # 访问视频页面
        video_url = f"https://www.bilibili.com/video/{bv_id}"
        print(f"[访问] {video_url}\n")
        driver.get(video_url)

        # 等待页面加载
        print("[等待] 页面加载中...")
        time.sleep(8)

        # 滚动到评论区位置
        print("[滚动] 定位评论区...")
        driver.execute_script("window.scrollTo(0, 4000);")
        time.sleep(5)

        # 收集用户
        users = []
        seen = set()
        last_count = 0
        scroll_count = 0
        max_scrolls = 100  # 最多滚动100次

        print("\n[开始] 滚动加载评论...")
        print("="*60)

        while scroll_count < max_scrolls:
            # 使用JavaScript提取用户信息
            new_users = driver.execute_script("""
                var users = [];
                var seen = arguments[0];

                // 查找所有链接
                var links = document.querySelectorAll('a[href*="space.bilibili.com"]');

                for (var i = 0; i < links.length; i++) {
                    try {
                        var href = links[i].getAttribute('href');

                        // 提取用户ID
                        var userId = null;
                        if (href.indexOf('//space.bilibili.com/') !== -1) {
                            var parts = href.split('//space.bilibili.com/')[1].split('/')[0].split('?');
                            userId = parts[0];
                        }

                        if (!userId || seen[userId]) continue;

                        var nickname = links[i].textContent.trim();
                        if (!nickname) continue;

                        // 查找对应的评论内容（在父元素中）
                        var comment = '';
                        var parent = links[i].closest('.reply-item, .root-reply, .reply-wrap, [class*="reply"]');

                        if (parent) {
                            var contentElem = parent.querySelector('.reply-content, .text-con, [class*="content"]');
                            if (contentElem) {
                                comment = contentElem.textContent || contentElem.innerText || '';
                            }
                        }

                        users.push({
                            user_id: String(userId),
                            nickname: nickname.substring(0, 50),
                            comment: comment.substring(0, 100)
                        });
                    } catch(e) {
                        console.log(e);
                    }
                }

                return users;
            """, {str(uid): True for uid in seen})

            # 添加新用户
            batch_new = 0
            for user_data in new_users:
                user_id = user_data.get('user_id')
                if user_id and user_id not in seen:
                    seen.add(user_id)
                    users.append(user_data)
                    batch_new += 1

            # 输出进度
            current_count = len(users)
            if current_count > last_count:
                print(f"[进度] 第{scroll_count+1}次滚动: 新增 {batch_new} 位，总计 {current_count} 位用户")
                last_count = current_count

            # 检查是否还有新内容
            if batch_new == 0:
                print(f"[提示] 第{scroll_count+1}次滚动无新用户")
            else:
                # 滚动到底部触发加载
                driver.execute_script("window.scrollBy(0, 1500);")

                # 尝试点击"查看更多评论"按钮
                try:
                    btn = driver.execute_script("""
                        var btns = document.querySelectorAll('button, a, [class*="more"], [class*="load"]');
                        for (var i = 0; i < btns.length; i++) {
                            var text = btns[i].textContent || '';
                            if (text.indexOf('更多') !== -1 || text.indexOf('查看') !== -1) {
                                if (btns[i].offsetParent !== null) {  // 可见
                                    return btns[i];
                                }
                            }
                        }
                        return null;
                    """)

                    if btn:
                        print("  [点击] 找到'查看更多'按钮")
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                except:
                    pass

            scroll_count += 1

            # 随机延迟
            time.sleep(random.uniform(2, 4))

        print("="*60)
        print(f"\n[完成] 滚动{scroll_count}次，共获取 {len(users)} 位用户")

        # 保存到文件
        if users:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{bv_id}_crawler_{timestamp}.json"
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

            # 显示部分用户
            print(f"\n[预览] 前20位用户:")
            for i, user in enumerate(users[:20], 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")

            if len(users) > 20:
                print(f"... 还有 {len(users)-20} 位用户")

        return users

    finally:
        print("\n[完成] 关闭浏览器")
        time.sleep(5)
        driver.quit()

def main():
    import sys

    if len(sys.argv) > 1:
        bv_id = sys.argv[1]
    else:
        bv_id = "BV1TRzZBuEg6"

    users = fetch_comments_crawler(bv_id)

    print(f"\n{'='*60}")
    print(f"总计: {len(users)} 位用户")
    print('='*60)

if __name__ == "__main__":
    main()
