#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版API获取：支持获取所有评论
"""

import time
import json
import requests
from datetime import datetime
from msg_config import USERS_DIR

def fetch_all_comments_api(bv_id, max_pages=500):
    """
    通过B站API获取所有评论（改进版）

    参数:
        bv_id: 视频BV号
        max_pages: 最大抓取页数
    """
    print(f"\n[API获取] 获取视频 {bv_id} 的所有评论...")
    print(f"[提示] 将持续抓取直到没有新评论或达到最大页数")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://www.bilibili.com/video/{bv_id}',
        'Accept': 'application/json',
    }

    try:
        # 获取视频信息
        print("[API] 获取视频信息...")
        video_info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
        response = requests.get(video_info_url, headers=headers, timeout=10)
        data = response.json()

        if data.get('code') != 0:
            print(f"[错误] 获取视频信息失败: {data}")
            return []

        aid = data['data']['aid']
        video_title = data['data'].get('title', '')
        print(f"[OK] 视频AID: {aid}")
        print(f"[OK] 视频标题: {video_title}")

        # 获取评论
        users = []
        page = 1
        seen = set()
        consecutive_empty = 0  # 连续空页计数
        max_consecutive_empty = 3  # 连续3页空则停止

        while page <= max_pages:
            try:
                # B站评论API - 支持cursor分页
                if page == 1:
                    # 第一页
                    comment_url = f"https://api.bilibili.com/x/v2/reply/main?"
                    comment_url += f"type=1&oid={aid}&mode=3&pn={page}&ps=20"
                else:
                    # 使用cursor模式继续分页
                    comment_url = f"https://api.bilibili.com/x/v2/reply/main?"
                    comment_url += f"type=1&oid={aid}&mode=3&pn={page}&ps=20"

                print(f"[API] 获取第{page}页评论...")
                response = requests.get(comment_url, headers=headers, timeout=15)
                comment_data = response.json()

                if comment_data.get('code') != 0:
                    error_msg = comment_data.get('message', '未知错误')
                    print(f"[警告] 第{page}页获取失败: {error_msg}")

                    # 如果是412错误（请求过于频繁），等待更长时间
                    if comment_data.get('code') == -412:
                        print(f"[提示] 遇到频率限制，等待30秒...")
                        time.sleep(30)
                        continue
                    else:
                        break

                replies = comment_data['data'].get('replies', [])

                if not replies:
                    consecutive_empty += 1
                    print(f"[提示] 第{page}页无评论 (空页计数: {consecutive_empty}/{max_consecutive_empty})")

                    if consecutive_empty >= max_consecutive_empty:
                        print(f"[提示] 连续{max_consecutive_empty}页无评论，停止抓取")
                        break

                    page += 1
                    time.sleep(2)
                    continue

                # 重置空页计数
                consecutive_empty = 0

                # 提取用户信息
                page_new_users = 0
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
                        page_new_users += 1

                print(f"  [OK] 本页获取 {len(replies)} 条评论，新增 {page_new_users} 位用户，累计 {len(users)} 位")

                # 检查总数
                total_count = comment_data['data'].get('page', {}).get('count', 0)
                if total_count > 0:
                    print(f"  [统计] 视频总评论数: {total_count}")

                page += 1

                # 动态延迟：每10页增加延迟
                base_delay = 2
                if page > 50:
                    base_delay = 3
                if page > 100:
                    base_delay = 5

                # 随机延迟
                delay = base_delay + time.time() % 2
                time.sleep(delay)

                # 每50页输出一次进度
                if page % 50 == 1:
                    print(f"\n[进度] 已抓取 {page-1} 页，获取 {len(users)} 位用户\n")

            except requests.exceptions.RequestException as e:
                print(f"[错误] 网络请求失败: {e}")
                print(f"[提示] 等待10秒后重试...")
                time.sleep(10)
                continue

            except Exception as e:
                print(f"[错误] 处理第{page}页时出错: {e}")
                import traceback
                traceback.print_exc()
                break

        # 保存到文件
        if users:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{bv_id}_all_{timestamp}.json"
            filepath = USERS_DIR / filename

            data = {
                "bv_id": bv_id,
                "video_title": video_title,
                "fetched_at": datetime.now().isoformat(),
                "total_users": len(users),
                "users": users
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"\n[保存] 用户列表已保存: {filepath}")

        print(f"\n[OK] 获取完成")
        print(f"[统计] 总计: {len(users)} 位用户，共 {page-1} 页")

        return users

    except Exception as e:
        print(f"[错误] 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    import sys

    if len(sys.argv) > 1:
        bv_id = sys.argv[1]
    else:
        bv_id = "BV1TRzZBuEg6"

    users = fetch_all_comments_api(bv_id, max_pages=500)

    if users:
        print(f"\n{'='*60}")
        print(f"获取到 {len(users)} 位用户:")
        print('='*60)

        for i, user in enumerate(users[:20], 1):
            print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
            if user.get('comment'):
                print(f"   评论: {user['comment'][:50]}")

        if len(users) > 20:
            print(f"\n... 还有 {len(users)-20} 位用户")

        print('='*60)

if __name__ == "__main__":
    main()
