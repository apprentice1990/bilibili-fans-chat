#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版评论爬取：使用B站API获取评论
"""

import time
import json
import requests
from datetime import datetime
from msg_config import USERS_DIR

def fetch_comments_via_api(bv_id, max_users=10):
    """
    通过B站API获取评论用户

    参数:
        bv_id: 视频BV号
        max_users: 最大获取用户数

    返回:
        list: 用户列表
    """
    print(f"\n[API获取] 获取视频 {bv_id} 的评论用户...")

    # B站评论API
    # 需要先获取oid（视频ID）
    video_info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"

    # 添加headers模拟浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://www.bilibili.com/video/{bv_id}',
        'Accept': 'application/json',
    }

    try:
        # 获取视频信息
        print("[API] 获取视频信息...")
        response = requests.get(video_info_url, headers=headers)
        data = response.json()

        if data.get('code') != 0:
            print(f"[错误] 获取视频信息失败: {data}")
            return []

        aid = data['data']['aid']
        print(f"[OK] 视频AID: {aid}")

        # 获取评论
        users = []
        page = 1
        seen = set()

        while len(users) < max_users:
            comment_url = f"https://api.bilibili.com/x/v2/reply/main?"
            comment_url += f"type=1&oid={aid}&mode=3&pn={page}&ps=20"

            print(f"[API] 获取第{page}页评论...")
            response = requests.get(comment_url, headers=headers)
            comment_data = response.json()

            if comment_data.get('code') != 0:
                print(f"[错误] 获取评论失败: {comment_data}")
                break

            replies = comment_data['data'].get('replies', [])

            if not replies:
                print(f"[提示] 没有更多评论了")
                break

            # 提取用户信息
            for reply in replies:
                member = reply.get('member', {})
                user_id = str(member.get('mid', ''))
                nickname = member.get('uname', '')
                content = reply.get('content', {}).get('message', '')
                like_count = reply.get('like', 0)

                # 去重
                if user_id and user_id not in seen:
                    seen.add(user_id)
                    users.append({
                        "user_id": user_id,
                        "nickname": nickname,
                        "comment": content[:100] if content else "",
                        "like_count": like_count
                    })

                    if len(users) % 10 == 0:
                        print(f"[进度] 已获取 {len(users)} 位用户...")

                    if len(users) >= max_users:
                        break

            page += 1
            time.sleep(1)  # API限流

        # 保存到文件
        if users:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{bv_id}_{timestamp}.json"
            filepath = USERS_DIR / filename

            data = {
                "bv_id": bv_id,
                "fetched_at": datetime.now().isoformat(),
                "total_users": len(users),
                "users": users
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[保存] 用户列表已保存: {filepath}")

        print(f"\n[OK] 获取完成")
        print(f"[统计] 总计: {len(users)} 位用户")

        return users

    except Exception as e:
        print(f"[错误] 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """主函数"""
    import sys

    # 从命令行获取BV号
    if len(sys.argv) > 1:
        bv_id = sys.argv[1]
    else:
        bv_id = input("请输入视频BV号: ").strip()

    if not bv_id.startswith('BV'):
        print("[错误] BV号格式错误")
        return

    # 获取评论
    users = fetch_comments_via_api(bv_id, max_users=100)

    if users:
        print(f"\n{'='*60}")
        print(f"获取到 {len(users)} 位用户:")
        print('='*60)

        for i, user in enumerate(users[:10], 1):  # 只显示前10个
            print(f"\n{i}. {user['nickname']}")
            print(f"   ID: {user['user_id']}")
            print(f"   评论: {user['comment']}")
            print(f"   点赞: {user['like_count']}")

        if len(users) > 10:
            print(f"\n... 还有 {len(users)-10} 位用户")

        print('='*60)

if __name__ == "__main__":
    main()
