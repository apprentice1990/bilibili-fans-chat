#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Playwright监听网络请求获取评论数据
基于MediaCrawler项目的实现思路
"""

import asyncio
import pickle
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Page

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

async def fetch_comments_playwright(bv_id, max_users=200):
    """通过Playwright监听网络请求获取评论"""
    print(f"\n[爬虫] Playwright监听网络请求")
    print(f"[视频] {bv_id}")
    print(f"[目标] 最多获取 {max_users} 位用户\n")

    users = {}
    seen = set()

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=False,
            args=['--window-size=1400,900']
        )

        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # 存储拦截到的评论数据
        comment_data = []

        # 设置网络监听
        async def handle_response(response):
            """拦截响应"""
            try:
                url = response.url

                # 检查是否是评论API
                if 'api.bilibili.com/x/v2/reply' in url:
                    print(f"[拦截] 发现评论API: {url[:80]}...")

                    # 获取响应体
                    try:
                        data = await response.json()

                        if data.get('code') == 0:
                            replies = data['data'].get('replies', [])

                            if replies:
                                print(f"  └─ 获取 {len(replies)} 条评论")

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

                                        print(f"     [{len(users)}] {nickname}")

                                        if len(users) >= max_users:
                                            break

                    except Exception as e:
                        print(f"  └─ 解析失败: {e}")

            except Exception as e:
                pass

        # 注册监听器
        page.on('response', handle_response)

        try:
            # 先访问B站主页
            print("[Cookies] 加载中...")
            await page.goto("https://www.bilibili.com")
            await asyncio.sleep(2)

            # 加载cookies
            cookie_path = Path(msg_config.COOKIE_FILE)
            if cookie_path.exists():
                with open(cookie_path, 'rb') as f:
                    cookies = pickle.load(f)

                for cookie in cookies:
                    try:
                        await context.add_cookie(cookie)
                    except:
                        pass

                await page.reload()
                await asyncio.sleep(2)

            # 访问视频
            video_url = f"https://www.bilibili.com/video/{bv_id}"
            print(f"\n[访问] {video_url}\n")
            await page.goto(video_url)
            await asyncio.sleep(10)

            # 滚动触发加载
            print("[滚动] 开始滚动加载评论...")
            print("="*60)

            scroll_count = 0
            max_scrolls = 100
            last_user_count = 0
            no_new_count = 0

            while scroll_count < max_scrolls and len(users) < max_users:
                # 滚动页面
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

                # 尝试点击"查看更多评论"
                try:
                    await page.click("text=查看更多评论", timeout=1000)
                    await asyncio.sleep(3)
                    print("  [点击] 查看更多评论")
                except:
                    pass

                # 尝试点击"加载更多"
                try:
                    load_more = await page.query_selector('button:has-text("更多"), button:has-text("加载")')
                    if load_more:
                        await load_more.click()
                        await asyncio.sleep(3)
                        print("  [点击] 加载更多按钮")
                except:
                    pass

                # 检查是否有新用户
                current_count = len(users)
                if current_count > last_user_count:
                    print(f"\n[进度] 滚动#{scroll_count+1}: 总计 {current_count} 位用户")
                    last_user_count = current_count
                    no_new_count = 0
                else:
                    no_new_count += 1

                # 如果连续15次没有新用户，可能到底了
                if no_new_count >= 15:
                    print(f"\n[提示] 连续{no_new_count}次无新用户，可能已加载全部评论")
                    break

                scroll_count += 1

            print("="*60)
            print(f"\n[完成] 滚动{scroll_count}次，获取 {len(users)} 位用户")

            # 保存结果
            if users:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{bv_id}_playwright_{timestamp}.json"
                filepath = Path(msg_config.USERS_DIR) / filename

                user_list = list(users.values())
                data = {
                    "bv_id": bv_id,
                    "fetched_at": datetime.now().isoformat(),
                    "total_users": len(user_list),
                    "users": user_list
                }

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                print(f"[保存] {filepath}")

                # 显示预览
                print(f"\n[预览] 所有用户:")
                for i, user in enumerate(user_list, 1):
                    print(f"{i}. {user['nickname']} (ID: {user['user_id']})")
                    if user.get('comment'):
                        comment = user['comment'][:40]
                        print(f"   评论: {comment}")

            return list(users.values())

        finally:
            print("\n[完成] 关闭浏览器")
            await asyncio.sleep(3)
            await browser.close()

def main():
    import sys
    import asyncio

    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1TRzZBuEg6"
    max_users = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    users = asyncio.run(fetch_comments_playwright(bv_id, max_users))
    print(f"\n总计: {len(users)} 位用户")

if __name__ == "__main__":
    main()
