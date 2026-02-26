#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API分页爬虫 - 直接调用B站评论API并处理分页
"""

import pickle
import time
import json
from pathlib import Path
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def bv_to_aid(bv_id):
    """BV号转AV号"""
    # 使用浏览器访问获取
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(f"https://www.bilibili.com/video/{bv_id}")
        time.sleep(3)

        aid = driver.execute_script("""
            var scripts = document.querySelectorAll('script');
            for (var i = 0; i < scripts.length; i++) {
                var text = scripts[i].textContent;
                var match = text.match(/"aid":(\d+)/);
                if (match) return match[1];
            }
            return null;
        """)

        return aid
    finally:
        driver.quit()

def fetch_comments_api_pagination(bv_id, max_users=500):
    """通过API分页获取评论"""
    print(f"\n[爬虫] API分页获取评论")
    print(f"[视频] {bv_id}")
    print(f"[目标] 最多获取 {max_users} 位用户\n")

    # 获取aid
    print("[步骤1] 获取视频aid...")
    aid = bv_to_aid(bv_id)

    if not aid:
        print("[错误] 无法获取aid")
        return []

    print(f"[成功] aid: {aid}\n")

    # 加载cookies
    print("[步骤2] 加载cookies...")
    cookie_path = Path(msg_config.COOKIE_FILE)

    with open(cookie_path, 'rb') as f:
        cookies = pickle.load(f)

    # 创建session
    session = requests.Session()

    for cookie in cookies:
        try:
            session.cookies.set(cookie['name'], cookie['value'])
        except:
            pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://www.bilibili.com/video/{bv_id}'
    }

    # 分页获取评论
    print("[步骤3] 分页获取评论...")
    print("="*60)

    users = {}
    seen = set()
    page = 1
    max_pages = 50  # 最多50页

    while page <= max_pages and len(users) < max_users:
        # 评论API URL（mode=3表示按热度排序）
        url = f"https://api.bilibili.com/x/v2/reply/main?oid={aid}&type=1&mode=3&pn={page}&ps=20"

        print(f"\n[请求] 页码 {page}: {url}")

        try:
            response = session.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('code') == 0:
                    page_info = data['data'].get('page', {})
                    total = page_info.get('count', 0)

                    replies = data['data'].get('replies', [])

                    if replies:
                        print(f"  └─ 获取 {len(replies)} 条评论 (总计: {total})")

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
                        print(f"[进度] 已获取 {len(users)} 位用户 (第{page}/{page_info.get('num', '?')}页)")

                    else:
                        print(f"  └─ 本页无评论")
                        break

                else:
                    print(f"  └─ API错误: {data.get('message', 'Unknown')}")
                    break

            else:
                print(f"  └─ HTTP错误: {response.status_code}")
                break

        except Exception as e:
            print(f"  └─ 请求失败: {e}")
            break

        # 检查是否已获取足够用户
        if len(users) >= max_users:
            print(f"\n[提示] 已达到目标用户数 {max_users}")
            break

        page += 1
        time.sleep(2)  # 延迟避免过快

    print("="*60)
    print(f"\n[完成] 获取 {len(users)} 位用户")

    # 保存
    if users:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{bv_id}_api_pagination_{timestamp}.json"
        filepath = Path(msg_config.USERS_DIR) / filename

        user_list = list(users.values())
        data = {
            "bv_id": bv_id,
            "aid": aid,
            "fetched_at": datetime.now().isoformat(),
            "total_users": len(user_list),
            "pages_fetched": page,
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

def main():
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    max_users = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    users = fetch_comments_api_pagination(bv_id, max_users)
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
