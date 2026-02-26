#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整获取所有评论用户 - 包括所有子回复（分页获取）
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
            return None
    except:
        return None

def fetch_sub_replies_full(session, aid, root_rpid, headers, seen, users):
    """获取某个主评论的所有子回复（分页）"""
    page = 1
    max_pages = 20  # 最多20页
    new_count = 0

    while page <= max_pages:
        url = f"https://api.bilibili.com/x/v2/reply/reply?oid={aid}&type=1&root={root_rpid}&pn={page}&ps=20"

        try:
            response = session.get(url, headers=headers, timeout=10)
            data = response.json()

            if data.get('code') == 0:
                sub_replies = data['data'].get('replies', [])

                if not sub_replies:
                    break

                page_new = 0
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
                        page_new += 1
                        print(f"       [{len(users)}] {nickname}")

                if page_new == 0:
                    # 本页没有新用户（都是重复的）
                    break

                page += 1
                time.sleep(0.3)  # 避免过快
            else:
                break

        except Exception as e:
            break

    return new_count

def fetch_all_comment_users_complete(bv_id, max_users=1000):
    """完整获取所有评论用户（主评论+所有子回复）"""
    print(f"\n[爬虫] 完整获取所有评论用户")
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
    print("[步骤3] 获取主评论（分页）...")
    print("="*60)

    users = {}
    seen = set()

    # 分页获取主评论
    page = 1
    page_size = 20  # 每页20条主评论
    max_pages = 50  # 最多50页主评论（1000条主评论）

    total_main_count = 0

    while page <= max_pages:
        print(f"\n[第{page}页] 获取主评论...")

        main_url = f"https://api.bilibili.com/x/v2/reply/main?oid={aid}&type=1&mode=3&pn={page}&ps={page_size}"

        try:
            response = session.get(main_url, headers=headers, timeout=10)
            data = response.json()

            if data.get('code') == 0:
                main_replies = data['data'].get('replies', [])

                if not main_replies:
                    print(f"[完成] 第{page}页没有更多主评论")
                    break

                print(f"[成功] 第{page}页获取到 {len(main_replies)} 条主评论")

                for i, reply in enumerate(main_replies, 1):
                    global_idx = total_main_count + i
                    member = reply.get('member', {})
                    user_id = str(member.get('mid', ''))
                    nickname = member.get('uname', '')
                    content = reply.get('content', {}).get('message', '')
                    count = reply.get('count', 0)  # 子回复数量
                    rpid = reply.get('rpid', '')

                    # 主评论用户
                    if user_id and user_id not in seen:
                        seen.add(user_id)
                        users[user_id] = {
                            "user_id": user_id,
                            "nickname": nickname,
                            "comment": content[:100] if content else ""
                        }

                    print(f"\n[{global_idx}] {nickname} (子回复: {count})")

                    # 获取所有子回复
                    if count > 0:
                        sub_new = fetch_sub_replies_full(session, aid, rpid, headers, seen, users)
                        print(f"    └─ 新增 {sub_new} 位用户")

                    # 检查是否达到目标
                    if len(users) >= max_users:
                        print(f"\n[提示] 已达到目标用户数 {max_users}")
                        break

                total_main_count += len(main_replies)
                print(f"\n[进度] 已处理 {total_main_count} 条主评论，获取到 {len(users)} 位用户")

                # 检查是否达到目标
                if len(users) >= max_users:
                    print(f"\n[完成] 已达到目标用户数 {max_users}")
                    break

                # 检查是否是最后一页
                cursor_data = data['data'].get('cursor')
                if cursor_data and cursor_data.get('is_end', False):
                    print(f"\n[完成] 已到最后一页")
                    break

                page += 1
                time.sleep(0.5)  # 避免请求过快
            else:
                print(f"[错误] API返回错误: {data.get('message', 'Unknown error')}")
                break

        except Exception as e:
            print(f"[错误] 获取主评论失败: {e}")
            import traceback
            traceback.print_exc()
            break

    print("="*60)
    print(f"\n[完成] 共获取 {len(users)} 位用户")

    # 保存
    if users:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{bv_id}_complete_{timestamp}.json"
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

        # 显示用户
        if len(user_list) <= 50:
            print(f"\n[所有用户] ({len(user_list)} 位):")
            for i, user in enumerate(user_list, 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
        else:
            print(f"\n[前40位用户] (共{len(user_list)}位):")
            for i, user in enumerate(user_list[:40], 1):
                print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
            print(f"\n... 还有 {len(user_list)-40} 位用户")

    return list(users.values())

def main():
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    max_users = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    users = fetch_all_comment_users_complete(bv_id, max_users)
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
