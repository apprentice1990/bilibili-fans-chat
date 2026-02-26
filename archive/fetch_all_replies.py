#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取所有评论用户 - 包括主评论和子回复
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

def get_aid_from_api(bv_id):
    """通过API获取aid"""
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

def fetch_all_comment_users(bv_id, max_users=1000):
    """获取所有评论用户（包括主评论和子回复）"""
    print(f"\n[爬虫] 获取所有评论用户（主评论+子回复）")
    print(f"[视频] {bv_id}")
    print(f"[目标] 最多获取 {max_users} 位用户\n")

    # 获取aid
    print("[步骤1] 获取aid...")
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

    # 获取所有评论
    print("[步骤3] 获取所有评论（主评论+子回复）...")
    print("="*60)

    users = {}
    seen = set()

    # 首先获取主评论
    print("\n[主评论] 获取中...")
    main_url = f"https://api.bilibili.com/x/v2/reply/main?oid={aid}&type=1&mode=3&pn=1&ps=20"

    try:
        response = session.get(main_url, headers=headers, timeout=10)
        data = response.json()

        if data.get('code') == 0:
            main_replies = data['data'].get('replies', [])

            for reply in main_replies:
                member = reply.get('member', {})
                user_id = str(member.get('mid', ''))
                nickname = member.get('uname', '')
                content = reply.get('content', {}).get('message', '')
                count = reply.get('count', 0)  # 子回复数量
                sub_replies = reply.get('replies', []) or []  # 子回复数组

                if user_id and user_id not in seen:
                    seen.add(user_id)
                    users[user_id] = {
                        "user_id": user_id,
                        "nickname": nickname,
                        "comment": content[:100] if content else ""
                    }

                print(f"  [{len(users)}] {nickname} (子回复: {count})")

                # 处理子回复
                if sub_replies:
                    print(f"    └─ 处理 {len(sub_replies)} 条子回复...")
                    for sub_reply in sub_replies:
                        sub_member = sub_reply.get('member', {})
                        sub_user_id = str(sub_member.get('mid', ''))
                        sub_nickname = sub_member.get('uname', '')
                        sub_content = sub_reply.get('content', {}).get('message', '')

                        if sub_user_id and sub_user_id not in seen:
                            seen.add(sub_user_id)
                            users[sub_user_id] = {
                                "user_id": sub_user_id,
                                "nickname": sub_nickname,
                                "comment": sub_content[:100] if sub_content else ""
                            }
                            print(f"       [{len(users)}] {sub_nickname}")

            print(f"\n[主评论] 完成，共 {len(main_replies)} 条")

    except Exception as e:
        print(f"[错误] 获取主评论失败: {e}")

    print("="*60)
    print(f"\n[完成] 共获取 {len(users)} 位用户")

    # 保存
    if users:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{bv_id}_all_replies_{timestamp}.json"
        filepath = Path(msg_config.USERS_DIR) / filename

        user_list = list(users.values())
        data = {
            "bv_id": bv_id,
            "aid": aid,
            "fetched_at": datetime.now().isoformat(),
            "total_users": len(user_list),
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
        else:
            print(f"\n[预览] 前30位用户:")
            for i, user in enumerate(user_list[:30], 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
            print(f"\n... 还有 {len(user_list)-30} 位用户")

    return list(users.values())

def fetch_sub_replies(session, aid, root_rpid, headers, seen, users):
    """获取子回复"""
    new_count = 0
    page = 1
    max_pages = 10  # 最多获取10页子回复

    while page <= max_pages:
        url = f"https://api.bilibili.com/x/v2/reply/reply?oid={aid}&type=1&root={root_rpid}&pn={page}&ps=20"

        try:
            response = session.get(url, headers=headers, timeout=10)
            data = response.json()

            if data.get('code') == 0:
                sub_replies = data['data'].get('replies', [])

                if not sub_replies:
                    break

                for reply in sub_replies:
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
                        print(f"       [{len(users)}] {nickname}")

                page += 1
                time.sleep(0.5)  # 避免过快

            else:
                break

        except Exception as e:
            break

    return new_count

def main():
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    max_users = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    users = fetch_all_comment_users(bv_id, max_users)
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
