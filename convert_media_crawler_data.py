#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将MediaCrawler爬取的数据转换为项目标准格式
"""

import json
from pathlib import Path
from datetime import datetime
import sys

def convert_media_crawler_to_standard(media_crawler_file, output_dir):
    """
    转换MediaCrawler的评论数据为标准格式

    Args:
        media_crawler_file: MediaCrawler导出的JSON文件路径
        output_dir: 输出目录
    """
    print(f"[转换] 读取MediaCrawler数据: {media_crawler_file}")

    # 读取MediaCrawler数据
    with open(media_crawler_file, 'r', encoding='utf-8') as f:
        comments = json.load(f)

    print(f"[信息] 总评论数: {len(comments)}")

    # 提取唯一用户
    users = {}
    for comment in comments:
        user_id = comment.get('user_id', '')
        if not user_id:
            continue

        # 如果用户已存在,只更新评论(保留第一条评论)
        if user_id not in users:
            users[user_id] = {
                "user_id": user_id,
                "nickname": comment.get('nickname', ''),
                "comment": comment.get('content', '')[:100]  # 截取前100字
            }

    print(f"[信息] 唯一用户数: {len(users)}")

    # 获取BV号(从文件名推断或使用默认)
    # 假设文件名包含日期,我们从其他地方获取BV号
    # 这里我们需要手动指定或从配置文件读取
    bv_id = "BV1hf4y1L763"  # 默认值

    # 创建标准格式数据
    user_list = list(users.values())

    data = {
        "bv_id": bv_id,
        "fetched_at": datetime.now().isoformat(),
        "total_users": len(user_list),
        "users": user_list
    }

    # 保存文件
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{bv_id}_mediacrawler_{timestamp}.json"
    filepath = output_path / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[成功] 数据已保存到: {filepath}")
    print(f"[统计] 共保存 {len(user_list)} 位用户")

    # 显示前20位用户
    print(f"\n[前20位用户]:")
    for i, user in enumerate(user_list[:20], 1):
        print(f"{i}. {user['nickname']} (ID: {user['user_id']})")

    if len(user_list) > 20:
        print(f"\n... 还有 {len(user_list)-20} 位用户")

    return filepath

def main():
    import argparse

    parser = argparse.ArgumentParser(description="转换MediaCrawler数据为标准格式")
    parser.add_argument(
        "--input",
        default="MediaCrawler/data/bili/json/detail_comments_2026-02-26.json",
        help="MediaCrawler导出的JSON文件路径"
    )
    parser.add_argument(
        "--output-dir",
        default="data/users",
        help="输出目录"
    )
    parser.add_argument(
        "--bv-id",
        default="BV1hf4y1L763",
        help="视频BV号"
    )

    args = parser.parse_args()

    input_file = Path(args.input)

    if not input_file.exists():
        print(f"[错误] 文件不存在: {input_file}")
        sys.exit(1)

    print("="*80)
    print("MediaCrawler数据转换工具")
    print("="*80)
    print()

    try:
        output_file = convert_media_crawler_to_standard(input_file, args.output_dir)

        print()
        print("="*80)
        print("转换完成!")
        print("="*80)
        print()
        print(f"输出文件: {output_file}")
        print()
        print("下一步: 使用该文件进行私信发送")
        print(f"命令: python run_campaign.py --users {output_file}")

    except Exception as e:
        print(f"[错误] 转换失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
