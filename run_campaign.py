#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站私信推广 - 完整流程
一键完成：抓取评论用户 + 发送私信
"""

import argparse
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def clean_user_files(keep_sent_records=True):
    """清理用户数据文件"""
    users_dir = Path(msg_config.USERS_DIR)

    if not users_dir.exists():
        print("[提示] 用户目录不存在，无需清理")
        return

    # 统计
    user_files = list(users_dir.glob("*.json"))
    total_size = sum(f.stat().st_size for f in user_files)

    print(f"\n[清理] 用户数据文件:")
    print(f"  文件数: {len(user_files)}")
    print(f"  总大小: {total_size / 1024:.1f} KB")

    # 删除用户文件
    for file in user_files:
        try:
            os.remove(file)
            print(f"  - 删除: {file.name}")
        except Exception as e:
            print(f"  ! 删除失败 {file.name}: {e}")

    print(f"[完成] 已清理 {len(user_files)} 个用户文件")

    # 保留发送记录
    if keep_sent_records:
        sent_dir = Path(msg_config.DATA_DIR) / "sent_records"
        if sent_dir.exists():
            sent_files = list(sent_dir.glob("*.json"))
            print(f"\n[保留] 发送记录: {len(sent_files)} 个文件")

def run_fetch_users(bv_id, max_users=1000, use_mediacrawler=True):
    """步骤1：抓取评论用户"""
    print("\n" + "="*60)
    print("步骤1：抓取评论用户")
    print("="*60)

    # 优先使用MediaCrawler
    if use_mediacrawler:
        print(f"\n[方案] 使用MediaCrawler (推荐)")
        users_file = fetch_from_mediacrawler(bv_id)
        if users_file:
            return users_file
        else:
            print(f"[提示] MediaCrawler数据未找到,回退到API方案")

    # 使用原API方案
    print(f"\n[方案] 使用原API方案")
    from fetch_all_replies_complete import fetch_all_comment_users_complete

    users = fetch_all_comment_users_complete(bv_id, max_users)

    # 返回最新的用户文件路径
    users_dir = Path(msg_config.USERS_DIR)
    if users_dir.exists():
        user_files = sorted(users_dir.glob(f"{bv_id}_complete_*.json"))
        if user_files:
            return user_files[-1]

    return None

def fetch_from_mediacrawler(bv_id):
    """从MediaCrawler获取用户数据"""
    import subprocess
    import shutil

    # 检查MediaCrawler是否存在
    mc_dir = Path(__file__).parent / "MediaCrawler"
    if not mc_dir.exists():
        print(f"[提示] MediaCrawler未安装")
        return None

    # 检查是否已存在转换后的数据
    users_dir = Path(msg_config.USERS_DIR)
    if users_dir.exists():
        existing_files = sorted(users_dir.glob(f"{bv_id}_mediacrawler_*.json"))
        if existing_files:
            print(f"[发现] 已存在MediaCrawler数据: {existing_files[-1].name}")
            use_existing = input("是否使用现有数据？(yes/no): ").strip().lower()
            if use_existing in ['yes', 'y']:
                return existing_files[-1]

    print(f"\n[运行] MediaCrawler爬虫...")
    print(f"[提示] 首次使用需扫码登录")

    # 检查convert_media_crawler_data.py是否存在
    converter = Path(__file__).parent / "convert_media_crawler_data.py"
    if not converter.exists():
        print(f"[错误] 数据转换工具不存在")
        return None

    # 询问用户是否运行MediaCrawler
    print(f"\n[提示] 将自动运行MediaCrawler并转换数据")
    confirm = input("是否继续？(yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        return None

    # 运行MediaCrawler
    print(f"\n[步骤1] 运行MediaCrawler...")
    mc_result = subprocess.run(
        ["python", "main.py", "--platform", "bili", "--lt", "qrcode", "--type", "detail"],
        cwd=mc_dir,
        capture_output=True
    )

    if mc_result.returncode != 0:
        print(f"[错误] MediaCrawler运行失败")
        print(mc_result.stdout.decode())
        print(mc_result.stderr.decode())
        return None

    print(f"[成功] MediaCrawler运行完成")

    # 转换数据
    print(f"\n[步骤2] 转换数据...")

    # 查找最新的MediaCrawler数据文件
    mc_data_dir = mc_dir / "data" / "bili" / "json"
    if not mc_data_dir.exists():
        print(f"[错误] MediaCrawler数据目录不存在")
        return None

    mc_files = sorted(mc_data_dir.glob("detail_comments_*.json"))
    if not mc_files:
        print(f"[错误] 未找到MediaCrawler数据文件")
        return None

    latest_mc_file = mc_files[-1]

    # 运行转换脚本
    convert_result = subprocess.run(
        ["python", "convert_media_crawler_data.py",
         "--input", str(latest_mc_file),
         "--output-dir", str(users_dir),
         "--bv-id", bv_id],
        cwd=Path(__file__).parent,
        capture_output=True
    )

    if convert_result.returncode != 0:
        print(f"[错误] 数据转换失败")
        print(convert_result.stdout.decode())
        print(convert_result.stderr.decode())
        return None

    # 返回转换后的文件
    converted_files = sorted(users_dir.glob(f"{bv_id}_mediacrawler_*.json"))
    if converted_files:
        return converted_files[-1]

    return None

def run_batch_send(users_file, video_url, title, skip_sent=True, dry_run=False):
    """步骤2：批量发送私信"""
    print("\n" + "="*60)
    print("步骤2：批量发送私信")
    print("="*60)

    import subprocess

    cmd = [
        "python", "batch_send.py",
        "--users", str(users_file),
        "--video-url", video_url,
        "--title", title
    ]

    if skip_sent:
        cmd.append("--skip-sent")

    if dry_run:
        cmd.append("--dry-run")

    print(f"\n[执行] {' '.join(cmd)}")

    # 执行发送脚本
    result = subprocess.run(cmd, cwd=Path(__file__).parent)

    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(
        description='B站私信推广 - 完整流程',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完整流程：清理旧数据 + 抓取用户 + 发送私信
  python run_campaign.py BV1TRzZBuEg6 --video-url "https://www.bilibili.com/video/BV1EYf4BQE7q" --title "忽然"

  # 保留已发记录，跳过已发送用户
  python run_campaign.py BV1TRzZBuEg6 --video-url "..." --title "..." --skip-sent

  # 试运行（不实际发送）
  python run_campaign.py BV1TRzZBuEg6 --video-url "..." --title "..." --dry-run

  # 只抓取用户，不发送
  python run_campaign.py BV1TRzZBuEg6 --fetch-only
        """
    )

    # 必需参数
    parser.add_argument('bv_id', help='要抓取评论的视频BV号')
    parser.add_argument('--video-url', required=True, help='推广的视频链接')
    parser.add_argument('--title', required=True, help='推广的视频标题')

    # 可选参数
    parser.add_argument('--max-users', type=int, default=1000,
                       help='最多抓取用户数（默认：1000）')
    parser.add_argument('--skip-sent', action='store_true', default=True,
                       help='跳过已发送用户（默认：True）')
    parser.add_argument('--no-skip-sent', dest='skip_sent', action='store_false',
                       help='不跳过已发送用户')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式（不实际发送）')
    parser.add_argument('--fetch-only', action='store_true',
                       help='只抓取用户，不发送私信')
    parser.add_argument('--keep-users', action='store_true',
                       help='保留已有用户文件（不删除）')
    parser.add_argument('--use-api', action='store_true',
                       help='使用原API方案（默认优先使用MediaCrawler）')

    args = parser.parse_args()

    print("\n" + "="*70)
    print(" "*15 + "B站私信推广工具 - 完整流程")
    print("="*70)
    print(f"\n[配置]")
    print(f"  源视频: {args.bv_id}")
    print(f"  推广视频: {args.video_url}")
    print(f"  推广标题: {args.title}")
    print(f"  最大用户数: {args.max_users}")
    print(f"  跳过已发送: {'是' if args.skip_sent else '否'}")
    print(f"  试运行: {'是' if args.dry_run else '否'}")
    print(f"  只抓取: {'是' if args.fetch_only else '否'}")

    # 确认
    if not args.dry_run and not args.fetch_only:
        print("\n" + "="*70)
        print("重要提示:")
        print("  1. 将删除当前所有用户数据文件")
        print("  2. 将保留发送记录（支持断点续传）")
        print("  3. 将发送私信给评论用户")
        print("="*70)

        confirm = input("\n确认开始？(yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("\n[取消] 操作已取消")
            return
    elif args.dry_run:
        print("\n[模式] 试运行模式（不会实际发送）")
    elif args.fetch_only:
        print("\n[模式] 只抓取用户模式")

    # 步骤0：清理旧用户数据
    if not args.keep_users:
        clean_user_files(keep_sent_records=True)

    # 步骤1：抓取评论用户
    users_file = run_fetch_users(args.bv_id, args.max_users, use_mediacrawler=not args.use_api)

    if not users_file:
        print("\n[错误] 未能获取用户数据")
        return

    print(f"\n[成功] 用户数据已保存: {users_file}")

    # 步骤2：发送私信
    if not args.fetch_only:
        success = run_batch_send(
            users_file,
            args.video_url,
            args.title,
            skip_sent=args.skip_sent,
            dry_run=args.dry_run
        )

        if success:
            print("\n" + "="*70)
            print(" "*20 + "推广流程完成！")
            print("="*70)
        else:
            print("\n[提示] 发送过程出现异常，请检查发送记录")
    else:
        print("\n[完成] 用户抓取完成（--fetch-only 模式，未发送）")

if __name__ == "__main__":
    main()
