#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium滚动加载所有评论
"""

import json
import pickle
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

def fetch_all_comments_selenium(bv_id):
    """使用Selenium滚动加载所有评论"""
    print(f"\n[Selenium] 获取视频 {bv_id} 的所有评论...")
    print(f"[提示] 将滚动页面到底部加载所有评论")

    # 初始化浏览器
    options = Options()
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        # 加载cookies
        print("\n[Cookies] 加载中...")
        driver.get("https://www.bilibili.com")
        time.sleep(2)

        cookie_path = msg_config.COOKIE_FILE
        with open(cookie_path, 'rb') as f:
            cookies = pickle.load(f)

        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                continue

        print(f"[OK] 已加载 {len(cookies)} 个cookies")
        driver.refresh()
        time.sleep(2)

        # 访问视频页面
        video_url = f"https://www.bilibili.com/video/{bv_id}"
        print(f"\n[访问] {video_url}")
        driver.get(video_url)
        time.sleep(5)

        # 滚动到评论区
        print("\n[滚动] 定位到评论区...")
        driver.execute_script("window.scrollTo(0, 5000);")
        time.sleep(3)

        # 收集用户
        users = []
        seen = set()
        last_count = 0
        no_change_count = 0
        max_no_change = 5  # 连续5次没有新用户则停止

        print("\n[开始] 滚动加载评论...")
        print("="*60)

        while no_change_count < max_no_change:
            # 查找评论元素
            try:
                # 使用JavaScript查找所有评论
                reply_data = driver.execute_script("""
                    var users = [];
                    var items = document.querySelectorAll('.reply-item, .root-reply-container, [class*="reply-item"]');

                    for (var i = 0; i < items.length; i++) {
                        try {
                            var item = items[i];

                            // 查找用户链接
                            var userLink = null;
                            var linkSelectors = ['.user-name', '.sub-user-name', '.name-text', 'a[href*="space.bilibili.com"]'];

                            for (var j = 0; j < linkSelectors.length; j++) {
                                var link = item.querySelector(linkSelectors[j]);
                                if (link) {
                                    userLink = link;
                                    break;
                                }
                            }

                            if (!userLink) continue;

                            var userId = userLink.getAttribute('data-user-id') ||
                                         userLink.getAttribute('data-id');
                            var nickname = userLink.textContent || userLink.innerText;

                            if (!userId) {
                                var href = userLink.getAttribute('href');
                                if (href && href.indexOf('//space.bilibili.com/') !== -1) {
                                    userId = href.split('//space.bilibili.com/')[1].split('/')[0].split('?')[0];
                                }
                            }

                            if (!userId) continue;

                            // 查找评论内容
                            var comment = '';
                            var contentSelectors = ['.reply-content', '.text-con', '.con', '[class*="content"]'];
                            for (var k = 0; k < contentSelectors.length; k++) {
                                var contentElem = item.querySelector(contentSelectors[k]);
                                if (contentElem) {
                                    comment = contentElem.textContent || contentElem.innerText || '';
                                    break;
                                }
                            }

                            users.push({
                                user_id: String(userId),
                                nickname: nickname.trim(),
                                comment: comment.substring(0, 100)
                            });
                        } catch(e) {}
                    }

                    return users;
                """)

                # 处理新用户
                for user_data in reply_data:
                    try:
                        user_id = user_data.get('user_id')
                        nickname = user_data.get('nickname')
                        comment = user_data.get('comment', '')

                        if not user_id or user_id in seen:
                            continue

                        seen.add(user_id)
                        users.append({
                            "user_id": user_id,
                            "nickname": nickname,
                            "comment": comment
                        })

                        if len(users) % 10 == 0:
                            print(f"[进度] 已获取 {len(users)} 位用户...")

                    except Exception as e:
                        continue

            except Exception as e:
                print(f"[错误] 查找评论失败: {e}")
                break

            # 检查是否有新用户
            current_count = len(users)
            if current_count == last_count:
                no_change_count += 1
                print(f"[提示] 无新用户 ({no_change_count}/{max_no_change})，继续滚动...")
            else:
                no_change_count = 0
                print(f"[新增] 本轮获取 {current_count - last_count} 位，总计 {current_count} 位")

            last_count = current_count

            # 滚动加载更多
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(random.uniform(1.5, 3))

            # 尝试点击"加载更多"按钮
            try:
                load_more_btn = driver.find_element(By.CSS_SELECTOR, '.load-more-btn, .view-more-btn, [class*="more"]')
                if load_more_btn.is_displayed():
                    load_more_btn.click()
                    print(f"[点击] 加载更多按钮")
                    time.sleep(2)
            except:
                pass

        print("="*60)
        print(f"\n[完成] 滚动结束，共获取 {len(users)} 位用户")

        # 保存到文件
        if users:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{bv_id}_selenium_{timestamp}.json"
            filepath = Path(msg_config.USERS_DIR) / filename

            data = {
                "bv_id": bv_id,
                "fetched_at": datetime.now().isoformat(),
                "total_users": len(users),
                "users": users
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[保存] {filepath}")

        return users

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

def main():
    import sys

    if len(sys.argv) > 1:
        bv_id = sys.argv[1]
    else:
        bv_id = "BV1TRzZBuEg6"

    users = fetch_all_comments_selenium(bv_id)

    if users:
        print(f"\n{'='*60}")
        print(f"总计 {len(users)} 位用户:")
        print('='*60)

        for i, user in enumerate(users[:20], 1):
            print(f"{i}. {user['nickname']} (ID: {user['user_id']})")

        if len(users) > 20:
            print(f"... 还有 {len(users)-20} 位用户")

        print('='*60)

if __name__ == "__main__":
    main()
