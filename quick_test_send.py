#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试:使用MediaCrawler数据发送私信
"""

import json
from pathlib import Path

def show_user_stats(users_file):
    """显示用户数据统计"""
    print("\n" + "="*60)
    print("用户数据统计")
    print("="*60)

    with open(users_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    bv_id = data.get('bv_id', '')
    total_users = data.get('total_users', 0)
    users = data.get('users', [])

    print(f"\nBV号: {bv_id}")
    print(f"唯一用户数: {total_users}")
    print(f"数据时间: {data.get('fetched_at', '')}")
    print(f"\n前10位用户:")

    for i, user in enumerate(users[:10], 1):
        print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
        if user.get('comment'):
            comment = user['comment'][:40] + '...' if len(user['comment']) > 40 else user['comment']
            print(f"   评论: {comment}")

    if len(users) > 10:
        print(f"\n... 还有 {len(users)-10} 位用户")

    return data

def main():
    print("\n" + "="*70)
    print(" "*20 + "快速测试 - MediaCrawler数据")
    print("="*70)

    # 查找MediaCrawler数据文件
    users_dir = Path("data/users")

    if not users_dir.exists():
        print("\n[错误] 用户数据目录不存在")
        return

    # 查找MediaCrawler数据
    mc_files = sorted(users_dir.glob("BV1hf4y1L763_mediacrawler_*.json"))

    if not mc_files:
        print("\n[错误] 未找到MediaCrawler数据文件")
        print("[提示] 请先运行: python convert_media_crawler_data.py")
        return

    latest_file = mc_files[-1]
    print(f"\n[发现] MediaCrawler数据文件: {latest_file.name}")

    # 显示统计信息
    data = show_user_stats(latest_file)

    # 询问是否继续
    print("\n" + "="*60)
    print("下一步: 发送私信")
    print("="*60)

    video_url = "https://www.bilibili.com/video/BV1TRzZBuEg6/"
    title = "热河"

    print(f"\n推广视频: {video_url}")
    print(f"推广标题: {title}")
    print(f"发送用户数: {data['total_users']}")

    confirm = input("\n是否开始发送？(yes/no): ").strip().lower()

    if confirm not in ['yes', 'y']:
        print("\n[取消] 操作已取消")
        return

    # 调用batch_send.py
    import subprocess

    cmd = [
        "python", "batch_send.py",
        "--users", str(latest_file),
        "--video-url", video_url,
        "--title", title,
        "--skip-sent"
    ]

    print(f"\n[执行] {' '.join(cmd)}")
    print("\n[提示] 开始发送...")

    result = subprocess.run(cmd, cwd=Path(__file__).parent)

    if result.returncode == 0:
        print("\n" + "="*60)
        print(" "*15 + "发送流程完成!")
        print("="*60)
    else:
        print("\n[提示] 发送过程出现异常")

if __name__ == "__main__":
    main()
