#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分页网络爬虫 - 通过拦截API响应获取所有评论（包括分页）
"""

import pickle
import time
import json
import re
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def fetch_comments_paginator(bv_id, max_users=500):
    """通过拦截网络请求获取所有分页评论"""
    print(f"\n[爬虫] 分页网络请求获取评论")
    print(f"[视频] {bv_id}")
    print(f"[目标] 最多获取 {max_users} 位用户\n")

    options = Options()
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

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

        # 访问视频获取aid
        video_url = f"https://www.bilibili.com/video/{bv_id}"
        print(f"[访问] {video_url}\n")
        driver.get(video_url)
        time.sleep(5)

        # 从页面获取aid
        aid = driver.execute_script("""
            // 尝试从多个位置获取aid
            var scripts = document.querySelectorAll('script');
            for (var i = 0; i < scripts.length; i++) {
                var text = scripts[i].textContent;
                var match = text.match(/"aid":(\d+)/);
                if (match) return match[1];
            }
            return null;
        """)

        if not aid:
            print("[错误] 无法获取aid")
            return []

        print(f"[信息] 获取到 aid: {aid}\n")

        # 收集所有API响应
        users = {}
        seen = set()
        api_urls = set()

        print("[开始] 滚动并拦截API请求...")
        print("="*60)

        scroll_count = 0
        max_scrolls = 100
        last_user_count = 0
        no_new_count = 0

        while scroll_count < max_scrolls and len(users) < max_users:
            # 获取网络日志
            logs = driver.get_log('performance')

            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']

                    if log['method'] == 'Network.responseReceived':
                        url = log['params']['response']['url']

                        # 检查是否是评论API
                        if 'api.bilibili.com/x/v2/reply' in url and url not in api_urls:
                            api_urls.add(url)

                            print(f"\n[API] 捕获: {url[:100]}...")

                            # 直接使用requests获取完整响应
                            try:
                                # 复制cookies
                                selenium_cookies = driver.get_cookies()
                                session = requests.Session()

                                for cookie in selenium_cookies:
                                    session.cookies.set(cookie['name'], cookie['value'])

                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                    'Referer': video_url
                                }

                                response = session.get(url, headers=headers, timeout=10)

                                if response.status_code == 200:
                                    data = response.json()

                                    if data.get('code') == 0:
                                        # 获取回复
                                        replies = data['data'].get('replies', [])

                                        # 也检查page中的replies
                                        if not replies and 'page' in data['data']:
                                            replies = data['data']['page'].get('replies', [])

                                        if replies:
                                            print(f"  └─ 获取 {len(replies)} 条评论")

                                            for reply in replies:
                                                member = reply.get('member', {})
                                                user_id = str(member.get('mid', ''))
                                                nickname = member.get('uname', '')
                                                content = reply.get('content', {}).get('message', '')

                                                if user_id and user_id not in seen:
                                                    seen.add(user_id)
                                                    users[user_id] = {
                                                        "user_id": user_id,
                                                        "nickname": nickname,
                                                        "comment": content[:100] if content else ""
                                                    }

                                                    print(f"     [{len(users)}] {nickname}")

                                            # 显示进度
                                            if len(users) > last_user_count:
                                                print(f"[进度] 总计 {len(users)} 位用户")
                                                last_user_count = len(users)
                                                no_new_count = 0

                            except Exception as e:
                                print(f"  └─ 获取失败: {e}")

                except:
                    continue

            # 滚动页面触发更多请求
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)

            # 尝试点击"查看更多评论"
            try:
                more_buttons = driver.find_elements("xpath",
                    "//*[contains(text(), '查看更多') or contains(text(), '更多评论')]")
                for btn in more_buttons:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        print("\n[点击] 查看更多评论")
                        time.sleep(3)
                        break
            except:
                pass

            # 检查进度
            if len(users) == last_user_count:
                no_new_count += 1
            else:
                no_new_count = 0

            # 连续30次无新用户则停止
            if no_new_count >= 30:
                print(f"\n[提示] 连续{no_new_count}次无新用户，可能已加载全部")
                break

            scroll_count += 1

        print("="*60)
        print(f"\n[完成] 捕获 {len(api_urls)} 个API请求")
        print(f"[完成] 获取 {len(users)} 位用户")

        # 保存
        if users:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{bv_id}_paginated_{timestamp}.json"
            filepath = Path(msg_config.USERS_DIR) / filename

            user_list = list(users.values())
            data = {
                "bv_id": bv_id,
                "fetched_at": datetime.now().isoformat(),
                "total_users": len(user_list),
                "api_urls_captured": len(api_urls),
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
                    comment = user['comment'][:50]
                    print(f"   评论: {comment}")

        return list(users.values())

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

def main():
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    max_users = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    users = fetch_comments_paginator(bv_id, max_users)
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
