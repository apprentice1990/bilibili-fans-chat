#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：查看B站视频页面的实际结构
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def main():
    print("\n[调试] 启动浏览器...")

    options = Options()
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        bv_id = "BV1TRzZBuEg6"
        url = f"https://www.bilibili.com/video/{bv_id}"

        print(f"[调试] 访问页面: {url}")
        driver.get(url)

        print("[提示] 等待10秒，请手动滚动到评论区...")
        time.sleep(10)

        # 获取页面源码
        page_source = driver.page_source

        # 保存到文件
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)

        print(f"[OK] 页面源码已保存到: page_source.html")
        print(f"[调试] 页面源码长度: {len(page_source)} 字符")

        # 查找可能的评论相关类名
        import re
        classes = re.findall(r'class="([^"]*reply[^"]*)"', page_source)
        unique_classes = list(set(classes))

        print(f"\n[调试] 找到的包含'reply'的类名 ({len(unique_classes)} 个):")
        for cls in unique_classes[:20]:
            print(f"  - {cls}")

        if len(unique_classes) > 20:
            print(f"  ... 还有 {len(unique_classes)-20} 个")

        # 查找用户信息相关类名
        user_classes = re.findall(r'class="([^"]*user[^"]*)"', page_source)
        unique_user_classes = list(set(user_classes))

        print(f"\n[调试] 找到的包含'user'的类名 ({len(unique_user_classes)} 个):")
        for cls in unique_user_classes[:20]:
            print(f"  - {cls}")

        if len(unique_user_classes) > 20:
            print(f"  ... 还有 {len(unique_user_classes)-20} 个")

        print("\n[提示] 浏览器将保持打开30秒，你可以手动查看页面...")
        time.sleep(30)

    finally:
        driver.quit()
        print("\n[调试] 浏览器已关闭")

if __name__ == "__main__":
    main()
