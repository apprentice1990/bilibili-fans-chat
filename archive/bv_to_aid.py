#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BV号转AV号算法 + API分页爬虫
"""

import pickle
import time
import json
from pathlib import Path
from datetime import datetime
import requests

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

# BV号转AV号的table
table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
tr = {c: i for i, c in enumerate(table)}
s = [11, 10, 3, 8, 4, 6]
xor = 177451812
add = 8728348608

def bv2av(bv):
    """BV号转AV号"""
    # BV号格式: BV + 10位字符
    if bv.startswith('BV'):
        bv = bv[2:]

    # 确保长度为12 (包含BV前缀的原始字符串)
    # 实际编码部分是10位，但我们需要完整的12位来计算
    # 重新构造: BV + 10位编码
    if len(bv) != 10:
        raise ValueError(f"Invalid BV ID: expected 10 chars after 'BV', got {len(bv)}")

    # BV号实际编码时会在前面加'BV'，变成12位
    # s数组是针对这12位的位置映射
    # 所以我们需要先构造12位字符串
    bv_encoded = 'BV' + bv  # 12位: B V + 10位编码

    r = 0
    for i, pos in enumerate(s):
        # pos是要提取的位置（0-based，针对12位字符串）
        # 但s数组的值是针对原始的排列方案
        # 正确的做法是：
        r += tr[bv_encoded[pos]] * (58 ** i)

    return (r - add) ^ xor

def get_aid_from_api(bv_id):
    """通过API获取aid"""
    # 使用B站Web接口获取视频信息
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://www.bilibili.com/video/{bv_id}'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if data.get('code') == 0:
            aid = data['data']['aid']
            return aid
        else:
            print(f"  API错误: {data.get('message')}")
            return None
    except Exception as e:
        print(f"  请求失败: {e}")
        return None

def fetch_comments_api_pagination(bv_id, max_users=500):
    """通过API分页获取评论"""
    print(f"\n[爬虫] API分页获取评论")
    print(f"[视频] {bv_id}")
    print(f"[目标] 最多获取 {max_users} 位用户\n")

    # 通过API获取aid
    print("[步骤1] 通过API获取aid...")
    aid = get_aid_from_api(bv_id)

    if not aid:
        print("[错误] 无法获取aid")
        return []

    print(f"[成功] AV{aid}\n")

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
    max_pages = 100  # 最多100页
    has_more = True

    while has_more and page <= max_pages and len(users) < max_users:
        # 评论API URL（mode=3表示按热度排序，mode=2表示按时间排序）
        url = f"https://api.bilibili.com/x/v2/reply/main?oid={aid}&type=1&mode=3&pn={page}&ps=20"

        print(f"\n[请求] 页码 {page}: {url}")

        try:
            response = session.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('code') == 0:
                    # 使用cursor代替page
                    cursor = data['data'].get('cursor', {})
                    total = cursor.get('all_count', 0)
                    is_end = cursor.get('is_end', False)
                    next_page = cursor.get('next', 0)

                    print(f"  └─ 总评论数: {total}, 是否结束: {is_end}")

                    replies = data['data'].get('replies', [])

                    if replies:
                        print(f"  └─ 本页 {len(replies)} 条评论")

                        new_count = 0
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
                                new_count += 1

                                print(f"     [{len(users)}] {nickname}")

                        # 显示进度
                        print(f"[进度] 本页新增 {new_count} 位，累计 {len(users)} 位用户")

                        # 检查是否最后一页
                        if is_end or next_page == 0:
                            print(f"\n[提示] 已到最后一页")
                            has_more = False

                    else:
                        print(f"  └─ 本页无评论，结束")
                        has_more = False

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
        time.sleep(1.5)  # 延迟避免过快

    print("="*60)
    print(f"\n[完成] 共获取 {len(users)} 位用户，{page} 页")

    # 保存
    if users:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{bv_id}_full_api_{timestamp}.json"
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
        if len(user_list) <= 50:
            print(f"\n[预览] 所有用户:")
            for i, user in enumerate(user_list, 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
                if user.get('comment'):
                    comment = user['comment'][:50]
                    print(f"   评论: {comment}")
        else:
            print(f"\n[预览] 前30位用户:")
            for i, user in enumerate(user_list[:30], 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
                if user.get('comment'):
                    comment = user['comment'][:50]
                    print(f"   评论: {comment}")
            print(f"\n... 还有 {len(user_list)-30} 位用户")

    return list(users.values())

def main():
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    max_users = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    users = fetch_comments_api_pagination(bv_id, max_users)
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
