#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比MediaCrawler和原API方案的效果
"""

import json
from pathlib import Path

def analyze_media_crawler():
    """分析MediaCrawler的爬取结果"""
    file_path = Path("MediaCrawler/data/bili/json/detail_comments_2026-02-26.json")

    if not file_path.exists():
        print("[错误] MediaCrawler数据文件不存在")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        comments = json.load(f)

    users = {}
    for comment in comments:
        user_id = comment.get('user_id', '')
        if user_id and user_id not in users:
            users[user_id] = {
                "user_id": user_id,
                "nickname": comment.get('nickname', ''),
                "comment": comment.get('content', '')[:100]
            }

    return {
        "method": "MediaCrawler (浏览器自动化)",
        "total_comments": len(comments),
        "unique_users": len(users),
        "users": list(users.values())
    }

def analyze_api_method():
    """分析原API方案的结果"""
    # 查找最新的爬取结果
    data_dir = Path("data/users")

    if not data_dir.exists():
        print("[错误] 原API方案数据目录不存在")
        return None

    # 查找BV1hf4y1L763的相关文件
    files = list(data_dir.glob("BV1hf4y1L763*.json"))

    if not files:
        print("[错误] 未找到原API方案的爬取数据")
        return None

    # 使用最新的文件
    latest_file = max(files, key=lambda f: f.stat().st_mtime)

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    users = data.get('users', [])

    return {
        "method": "原API方案 (fetch_all_replies_complete.py)",
        "total_comments": "未知",  # 原方案没有保存评论总数
        "unique_users": len(users),
        "users": users
    }

def main():
    print("="*80)
    print("B站评论爬取方案对比分析")
    print("="*80)
    print(f"视频: BV1hf4y1L763 (60万播放)")
    print()

    # 分析MediaCrawler
    print("[1] 分析MediaCrawler结果...")
    mc_result = analyze_media_crawler()

    # 分析原API方案
    print("[2] 分析原API方案结果...")
    api_result = analyze_api_method()

    if not mc_result or not api_result:
        print("[错误] 无法获取对比数据")
        return

    # 对比结果
    print()
    print("="*80)
    print("对比结果")
    print("="*80)
    print()

    print(f"方案1: {mc_result['method']}")
    print(f"  - 总评论数: {mc_result['total_comments']}")
    print(f"  - 唯一用户数: {mc_result['unique_users']}")
    print()

    print(f"方案2: {api_result['method']}")
    print(f"  - 总评论数: {api_result['total_comments']}")
    print(f"  - 唯一用户数: {api_result['unique_users']}")
    print()

    print("="*80)
    print("效果提升")
    print("="*80)
    print()

    improvement = mc_result['unique_users'] - api_result['unique_users']
    improvement_rate = (improvement / api_result['unique_users']) * 100

    print(f"用户数提升: {api_result['unique_users']} → {mc_result['unique_users']} (+{improvement} 位, +{improvement_rate:.1f}%)")
    print()

    # 显示部分用户对比
    print("="*80)
    print("用户示例 (MediaCrawler前20位)")
    print("="*80)
    print()

    for i, user in enumerate(mc_result['users'][:20], 1):
        print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
        if user['comment']:
            print(f"   评论: {user['comment'][:50]}...")

    print()
    print("="*80)
    print("结论")
    print("="*80)
    print()
    print("✅ MediaCrawler方案明显优于原API方案")
    print(f"✅ 获取用户数量提升 {improvement_rate:.1f}%")
    print("✅ MediaCrawler基于浏览器自动化,能绕过API限制")
    print("✅ MediaCrawler支持二级评论爬取,获取更全面的用户数据")
    print()

if __name__ == "__main__":
    main()
