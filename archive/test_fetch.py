#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：只测试评论爬取功能，不发送私信
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import msg_config
from comment_fetcher import CommentFetcher

def main():
    print("\n" + "#"*60)
    print("# B站私信推广工具 - 测试模式")
    print("#"*60)
    print("此模式仅测试评论爬取功能，不会发送私信\n")

    # 初始化浏览器
    print("[浏览器] 正在初始化...")
    options = Options()
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        # 获取评论用户
        bv_id = "BV1TRzZBuEg6"
        print(f"\n[测试] 获取视频 {bv_id} 的评论用户...")

        fetcher = CommentFetcher(driver)
        users = fetcher.fetch_comments(bv_id, max_users=10, save_to_file=True)

        if users:
            print(f"\n[成功] 获取到 {len(users)} 位用户:")
            print("="*60)

            for i, user in enumerate(users, 1):
                print(f"{i}. {user['nickname']}")
                print(f"   ID: {user['user_id']}")
                print(f"   评论: {user['comment']}")
                print(f"   点赞: {user['like_count']}")
                print()

            print("="*60)
            print(f"\n完整数据已保存到: data/users/")
            print("\n[提示] 测试完成！如需实际发送，请运行主程序。")
        else:
            print("\n[错误] 未获取到任何用户")

    finally:
        print("\n按Enter键关闭浏览器...")
        input()
        driver.quit()
        print("[浏览器] 已关闭")

if __name__ == "__main__":
    main()
