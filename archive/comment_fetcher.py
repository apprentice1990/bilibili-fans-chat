#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评论爬取模块
从B站视频页面爬取评论用户信息
"""

import time
import random
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from msg_config import (
    VIDEO_URL,
    MAX_USERS_PER_VIDEO,
    MIN_LIKES,
    EXCLUDE_OFFICIAL,
    OFFICIAL_KEYWORDS,
    COMMENT_ITEM_SELECTOR,
    COMMENT_ITEM_SELECTORS,
    USER_INFO_SELECTOR,
    USER_INFO_SELECTORS,
    USER_ID_ATTR,
    COMMENT_CONTENT_SELECTOR,
    COMMENT_CONTENT_SELECTORS,
    USERS_DIR
)


class CommentFetcher:
    """评论爬取器"""

    def __init__(self, driver):
        """
        初始化评论爬取器

        参数:
            driver: Selenium WebDriver实例
        """
        self.driver = driver

    def _find_elements_with_fallback(self, selectors):
        """
        使用多个选择器尝试查找元素

        参数:
            selectors: 选择器列表

        返回:
            list: 找到的元素列表，如果都失败返回空列表
        """
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except:
                continue
        return []

    def fetch_comments(self, bv_id, max_users=None, save_to_file=True):
        """
        获取视频评论用户

        参数:
            bv_id: 视频BV号
            max_users: 最大获取用户数（默认使用配置值）
            save_to_file: 是否保存到文件

        返回:
            list: 用户信息列表
        """
        if max_users is None:
            max_users = MAX_USERS_PER_VIDEO

        print(f"\n[评论爬取] 开始获取视频 {bv_id} 的评论用户...")
        print(f"[评论爬取] 目标用户数: {max_users}")

        # 访问视频页面
        url = VIDEO_URL.format(bv_id)
        print(f"[评论爬取] 访问页面: {url}")

        self.driver.get(url)
        time.sleep(random.uniform(3, 5))

        # 尝试滚动到评论区
        print("[提示] 滚动到评论区...")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 3))

        users = []
        seen = set()  # 用于去重
        scroll_count = 0
        max_scrolls = 50  # 最多滚动50次

        try:
            while len(users) < max_users and scroll_count < max_scrolls:
                # 滚动加载评论
                self.driver.execute_script("window.scrollBy(0, 800);")
                scroll_count += 1

                # 随机延迟，模拟真实用户
                time.sleep(random.uniform(2, 4))

                # 查找评论元素（使用多重选择器）
                try:
                    comment_items = self._find_elements_with_fallback(COMMENT_ITEM_SELECTORS)

                    if not comment_items:
                        # 如果还是找不到，尝试打印页面源码的一部分来调试
                        if scroll_count == 1:
                            print("[调试] 评论选择器未找到元素")
                            print(f"[调试] 当前页面URL: {self.driver.current_url}")
                            print(f"[调试] 页面标题: {self.driver.title}")
                        continue

                    # 提取用户信息
                    for item in comment_items:
                        try:
                            # 获取用户链接
                            user_link = item.find_element(By.CSS_SELECTOR, USER_INFO_SELECTOR)

                            # 获取用户ID（优先从data属性获取）
                            user_id = user_link.get_attribute(USER_ID_ATTR)

                            if not user_id:
                                # 如果没有data属性，从URL中提取
                                user_url = user_link.get_attribute("href")
                                user_id = user_url.split("/")[-1]

                            # 去重检查
                            if user_id in seen:
                                continue

                            # 获取昵称
                            nickname = user_link.text.strip()

                            # 排除官方账号
                            if EXCLUDE_OFFICIAL and self._is_official_account(nickname):
                                continue

                            # 获取评论内容
                            try:
                                comment_elem = item.find_element(By.CSS_SELECTOR, COMMENT_CONTENT_SELECTOR)
                                comment = comment_elem.text.strip()
                            except:
                                comment = ""

                            # 获取点赞数
                            try:
                                like_elem = item.find_element(By.CSS_SELECTOR, ".reply-action like")
                                like_count = int(like_elem.text.strip()) if like_elem.text.strip().isdigit() else 0
                            except:
                                like_count = 0

                            # 过滤低赞评论
                            if MIN_LIKES > 0 and like_count < MIN_LIKES:
                                continue

                            # 添加到列表
                            user_info = {
                                "user_id": user_id,
                                "nickname": nickname,
                                "comment": comment[:100] if comment else "",  # 截取前100字
                                "like_count": like_count,
                            }

                            users.append(user_info)
                            seen.add(user_id)

                            # 进度提示
                            if len(users) % 10 == 0:
                                print(f"[进度] 已获取 {len(users)} 位用户...")

                            # 达到目标数量，停止
                            if len(users) >= max_users:
                                break

                        except Exception as e:
                            # 单个评论提取失败，继续处理下一个
                            continue

                except Exception as e:
                    print(f"[警告] 滚动{scroll_count}次后出错: {e}")
                    continue

            # 爬取完成
            print(f"\n[OK] 评论爬取完成")
            print(f"[统计] 获取用户数: {len(users)}")
            print(f"[统计] 滚动次数: {scroll_count}")

            # 保存到文件
            if save_to_file and users:
                self._save_to_file(bv_id, users)

            return users

        except Exception as e:
            print(f"[错误] 评论爬取失败: {e}")
            import traceback
            traceback.print_exc()
            return users

    def _is_official_account(self, nickname):
        """
        判断是否为官方账号

        参数:
            nickname: 用户昵称

        返回:
            bool: 是否为官方账号
        """
        for keyword in OFFICIAL_KEYWORDS:
            if keyword in nickname:
                return True
        return False

    def _save_to_file(self, bv_id, users):
        """
        保存用户列表到文件

        参数:
            bv_id: 视频BV号
            users: 用户列表
        """
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

    @staticmethod
    def load_from_file(filepath):
        """
        从文件加载用户列表

        参数:
            filepath: 文件路径

        返回:
            list: 用户列表
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get('users', [])


if __name__ == "__main__":
    # 测试代码（需要手动提供driver）
    print("评论爬取模块")
    print("="*60)
    print("请通过主程序调用此模块")
