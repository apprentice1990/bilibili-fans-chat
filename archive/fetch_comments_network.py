#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium监听网络请求获取评论数据
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

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def fetch_comments_network(bv_id):
    """通过监听网络请求获取评论"""
    print(f"\n[爬虫] 监听网络请求获取评论")
    print(f"[视频] {bv_id}\n")

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

        # 访问视频
        video_url = f"https://www.bilibili.com/video/{bv_id}"
        print(f"[访问] {video_url}\n")
        driver.get(video_url)
        time.sleep(10)

        # 滚动到评论区触发加载
        print("[滚动] 触发评论加载...")
        driver.execute_script("window.scrollTo(0, 4000);")
        time.sleep(5)

        # 收集所有网络请求中的评论数据
        users = {}
        seen = set()

        print("[开始] 收集网络请求中的评论数据...")
        print("="*60)

        for scroll_i in range(20):
            # 获取网络日志
            logs = driver.get_log('performance')

            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']

                    # 查找评论API请求
                    if log['method'] == 'Network.responseReceived':
                        url = log['params']['response']['url']

                        # 检查是否是评论API
                        if 'api.bilibili.com/x/v2/reply' in url or 'api.bilibili.com/x/v2/reply/main' in url:
                            request_id = log['params']['requestId']

                            # 获取响应体
                            try:
                                response_body = driver.execute_script("""
                                    var requestId = arguments[0];
                                    var entries = performance.getEntries();
                                    for (var i = 0; i < entries.length; i++) {
                                        if (entries[i].name.indexOf('api.bilibili.com/x/v2/reply') !== -1) {
                                            return entries[i].response;
                                        }
                                    }
                                    return null;
                                """, request_id)

                                # 尝试通过fetch获取
                                import requests
                                headers = {
                                    'User-Agent': 'Mozilla/5.0',
                                    'Referer': f'https://www.bilibili.com/video/{bv_id}'
                                }

                                try:
                                    api_resp = requests.get(url, headers=headers, timeout=5)
                                    if api_resp.status_code == 200:
                                        data = api_resp.json()

                                        if data.get('code') == 0:
                                            replies = data['data'].get('replies', [])

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

                                            if replies:
                                                print(f"[API] 从网络请求获取 {len(replies)} 条评论，累计 {len(users)} 位用户")

                                except:
                                    pass

                            except Exception as e:
                                pass

                except:
                    continue

            # 继续滚动触发更多加载
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)

            # 点击加载更多
            try:
                driver.execute_script("""
                    var btns = document.querySelectorAll('button, a, div');
                    for (var i = 0; i < btns.length; i++) {
                        var text = btns[i].textContent || '';
                        if (text.indexOf('更多') !== -1 || text.indexOf('展开') !== -1) {
                            if (btns[i].offsetParent !== null) {
                                btns[i].click();
                                break;
                            }
                        }
                    }
                """)
                time.sleep(2)
            except:
                pass

        print("="*60)
        print(f"\n[完成] 从网络请求获取 {len(users)} 位用户")

        # 转换为列表
        user_list = list(users.values())

        # 保存
        if user_list:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{bv_id}_network_{timestamp}.json"
            filepath = Path(msg_config.USERS_DIR) / filename

            data = {
                "bv_id": bv_id,
                "fetched_at": datetime.now().isoformat(),
                "total_users": len(user_list),
                "users": user_list
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[保存] {filepath}")

            # 显示用户
            print(f"\n[预览] 前30位用户:")
            for i, user in enumerate(user_list[:30], 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
                if user.get('comment'):
                    print(f"   评论: {user['comment'][:40]}")

            if len(user_list) > 30:
                print(f"... 还有 {len(user_list)-30} 位用户")

        return user_list

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

def main():
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    users = fetch_comments_network(bv_id)
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
