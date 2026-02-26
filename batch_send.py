#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量发送私信脚本（优化版）
功能：
1. 记录已发送用户，避免重复发送
2. 支持外部提供视频链接
3. 保存发送记录
"""

import json
import pickle
import time
import random
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.insert(0, str(Path(__file__).parent))
import msg_config

# 发送记录目录
SENT_RECORDS_DIR = Path(msg_config.DATA_DIR) / "sent_records"

def load_sent_users(video_url=None):
    """加载已发送用户记录"""
    if not SENT_RECORDS_DIR.exists():
        SENT_RECORDS_DIR.mkdir(parents=True)

    sent_users = set()

    # 加载所有记录文件
    for record_file in SENT_RECORDS_DIR.glob("sent_*.json"):
        try:
            with open(record_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
                # 如果指定了视频链接，只返回该视频的记录
                if video_url is None or records.get('video_url') == video_url:
                    for record in records.get('sent_list', []):
                        sent_users.add(record['user_id'])
        except:
            continue

    return sent_users

def init_sent_record(video_url, total_users):
    """初始化发送记录文件"""
    if not SENT_RECORDS_DIR.exists():
        SENT_RECORDS_DIR.mkdir(parents=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sent_{timestamp}.json"
    filepath = SENT_RECORDS_DIR / filename

    record = {
        "video_url": video_url,
        "started_at": datetime.now().isoformat(),
        "total_users": total_users,
        "total_sent": 0,
        "total_skipped": 0,
        "total_failed": 0,
        "sent_list": [],
        "skipped_list": [],
        "failed_list": []
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    print(f"[记录] 已创建记录文件: {filepath}")
    return filepath

def append_to_record(filepath, record_type, user_data):
    """追加单条记录到文件"""
    try:
        # 读取当前记录
        with open(filepath, 'r', encoding='utf-8') as f:
            record = json.load(f)

        # 追加新记录
        if record_type == 'sent':
            record['sent_list'].append(user_data)
            record['total_sent'] = len(record['sent_list'])
        elif record_type == 'skipped':
            record['skipped_list'].append(user_data)
            record['total_skipped'] = len(record['skipped_list'])
        elif record_type == 'failed':
            record['failed_list'].append(user_data)
            record['total_failed'] = len(record['failed_list'])

        # 更新时间戳
        record['updated_at'] = datetime.now().isoformat()

        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"[警告] 保存记录失败: {e}")
        return False

def finalize_sent_record(filepath):
    """完成记录，添加结束时间"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            record = json.load(f)

        record['completed_at'] = datetime.now().isoformat()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        print(f"[记录] 发送记录已保存: {filepath}")
    except Exception as e:
        print(f"[警告] 完成记录失败: {e}")

def send_to_user(driver, user_id, message):
    """向用户发送私信"""
    try:
        # 导航到私信页面
        msg_url = f"https://message.bilibili.com/#/whisper/mid{user_id}"
        driver.get(msg_url)
        time.sleep(5)

        # 完整发送流程
        result = driver.execute_script("""
            var message = arguments[0];

            // 1. 关闭弹窗
            var closeBtn = document.querySelector('.bili-popup__header__close');
            if (closeBtn) {
                closeBtn.click();
            }

            // 2. 找到contenteditable输入框
            var editables = document.querySelectorAll('[contenteditable="true"]');
            var targetElement = null;

            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    targetElement = editables[i];
                    break;
                }
            }

            if (!targetElement) {
                return {success: false, error: '未找到contenteditable输入框'};
            }

            // 3. 聚焦并输入消息
            targetElement.focus();
            targetElement.click();
            targetElement.textContent = message;

            // 触发事件
            var events = ['input', 'change', 'keyup'];
            events.forEach(function(type) {
                var event = new Event(type, {bubbles: true});
                targetElement.dispatchEvent(event);
            });

            // 4. 发送（尝试多种方法）
            // 方法1: 查找发送按钮
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.trim();
                if (text.indexOf('发送') !== -1 && !buttons[i].disabled) {
                    buttons[i].click();
                    return {success: true, method: 'button'};
                }
            }

            // 方法2: Ctrl+Enter
            var ctrlEnter = new KeyboardEvent('keydown', {
                key: 'Enter', code: 'Enter', keyCode: 13,
                bubbles: true, ctrlKey: true
            });
            targetElement.dispatchEvent(ctrlEnter);

            // 方法3: 普通Enter
            var enter = new KeyboardEvent('keydown', {
                key: 'Enter', code: 'Enter', keyCode: 13,
                bubbles: true
            });
            targetElement.dispatchEvent(enter);

            return {success: true, method: 'keyboard'};
        """, message)

        time.sleep(2)

        # 验证
        check = driver.execute_script("""
            var editables = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editables.length; i++) {
                var rect = editables[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    return {
                        length: editables[i].textContent.length,
                        empty: editables[i].textContent.length === 0
                    };
                }
            }
            return {error: 'check failed'};
        """)

        if check.get('empty', False):
            return {"status": "success"}
        else:
            return {"status": "failed", "reason": f"未清空，长度: {check.get('length')}"}

    except Exception as e:
        return {"status": "failed", "reason": str(e)[:200]}

def main():
    import argparse

    parser = argparse.ArgumentParser(description='批量发送B站私信')
    parser.add_argument('--users', required=True, help='用户JSON文件路径')
    parser.add_argument('--video-url', required=True, help='推广视频链接')
    parser.add_argument('--title', default='新视频', help='视频标题（用于消息模板）')
    parser.add_argument('--skip-sent', action='store_true', help='跳过已发送用户（仅检查当前视频）')
    parser.add_argument('--dry-run', action='store_true', help='试运行（不实际发送）')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("批量发送私信脚本（优化版）")
    print("="*60)

    # 加载用户
    users_file = Path(args.users)
    if not users_file.exists():
        print(f"[错误] 用户文件不存在: {users_file}")
        return

    with open(users_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    all_users = data['users']

    print(f"[OK] 已加载 {len(all_users)} 位用户")

    # 加载已发送用户记录
    sent_users = set()
    if args.skip_sent:
        sent_users = load_sent_users(args.video_url)
        print(f"[记录] 已发送记录: {len(sent_users)} 位用户")

    # 过滤用户
    users_to_send = []
    skipped_users = []

    for user in all_users:
        if user['user_id'] in sent_users:
            skipped_users.append(user)
        else:
            users_to_send.append(user)

    print(f"[过滤] 待发送: {len(users_to_send)} 位，已跳过: {len(skipped_users)} 位")

    if len(users_to_send) == 0:
        print("\n[提示] 没有需要发送的用户")
        return

    # 准备消息
    template_file = Path("templates/message_template.txt")
    if template_file.exists():
        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()
    else:
        template = msg_config.DEFAULT_MESSAGE_TEMPLATE

    message = template.format(title=args.title, video_url=args.video_url)

    print(f"\n[消息] 预览:")
    print(message[:100] + "..." if len(message) > 100 else message)
    print(f"\n[视频] {args.video_url}")

    # 显示待发送用户
    print(f"\n[待发送用户] ({len(users_to_send)} 位):")
    for i, user in enumerate(users_to_send[:10], 1):
        print(f"  {i}. {user['nickname']} (ID: {user['user_id']})")
    if len(users_to_send) > 10:
        print(f"  ... 还有 {len(users_to_send)-10} 位用户")

    # 确认
    if not args.dry_run:
        confirm = input("\n开始批量发送？(yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("[取消] 已取消")
            return

    # 试运行模式
    if args.dry_run:
        print("\n[试运行] 不会实际发送消息")
        print(f"[统计] 将发送给 {len(users_to_send)} 位用户")
        return

    # 初始化浏览器
    print("\n[浏览器] 启动...")
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
        print("\n[Cookies] 加载...")
        cookie_path = msg_config.COOKIE_FILE

        driver.get("https://www.bilibili.com")
        time.sleep(2)

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

        # 批量发送配置
        BATCH_SIZE = 10  # 每批用户数
        INTRA_BATCH_MIN_DELAY = 0   # 批内最小延迟（秒）
        INTRA_BATCH_MAX_DELAY = 10  # 批内最大延迟（秒）
        INTER_BATCH_MIN_DELAY = 100 # 批间最小延迟（秒）
        INTER_BATCH_MAX_DELAY = 200 # 批间最大延迟（秒）

        # 初始化记录文件（在开始发送前创建）
        record_file = init_sent_record(args.video_url, len(users_to_send))

        # 立即记录所有跳过的用户
        if skipped_users:
            print(f"\n[记录] 正在记录 {len(skipped_users)} 位跳过的用户...")
            for user in skipped_users:
                record = {
                    "user_id": user['user_id'],
                    "nickname": user['nickname'],
                    "reason": "已发送过（跳过）"
                }
                append_to_record(record_file, 'skipped', record)
            print(f"[OK] 已记录 {len(skipped_users)} 位跳过用户")

        # 批量发送
        total_batches = (len(users_to_send) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_idx in range(total_batches):
            start_idx = batch_idx * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(users_to_send))
            batch_users = users_to_send[start_idx:end_idx]

            print(f"\n{'='*60}")
            print(f"批次 {batch_idx+1}/{total_batches} ({len(batch_users)} 位用户)")
            print(f"{'='*60}")

            # 发送当前批次
            for batch_pos, user in enumerate(batch_users):
                global_idx = start_idx + batch_pos
                print(f"\n[{global_idx+1}/{len(users_to_send)}] {user['nickname']} (ID: {user['user_id']})")

                result = send_to_user(driver, user['user_id'], message)

                # 准备记录数据
                record = {
                    "user_id": user['user_id'],
                    "nickname": user['nickname'],
                    "sent_at": datetime.now().isoformat()
                }

                # 立即保存记录
                if result['status'] == 'success':
                    append_to_record(record_file, 'sent', record)
                    print(f"  [OK] 成功！[已记录]")
                else:
                    record['reason'] = result['reason']
                    append_to_record(record_file, 'failed', record)
                    print(f"  [FAIL] {result['reason']} [已记录]")

                # 批内用户间延迟（0-10秒随机）
                if batch_pos < len(batch_users) - 1:  # 不是本批次最后一个
                    delay = random.randint(INTRA_BATCH_MIN_DELAY, INTRA_BATCH_MAX_DELAY)
                    print(f"  [等待] {delay}秒...")
                    time.sleep(delay)

            # 批次间延迟（100-200秒随机）
            if batch_idx < total_batches - 1:  # 不是最后一批
                delay = random.randint(INTER_BATCH_MIN_DELAY, INTER_BATCH_MAX_DELAY)
                print(f"\n{'='*60}")
                print(f"[批次完成] 等待 {delay}秒 后继续下一批次...")
                print(f"[预计] {datetime.fromtimestamp(time.time() + delay).strftime('%H:%M:%S')} 继续")
                print(f"{'='*60}")
                time.sleep(delay)

        # 完成记录（添加结束时间）
        finalize_sent_record(record_file)

        # 读取最终统计
        with open(record_file, 'r', encoding='utf-8') as f:
            final_record = json.load(f)

        sent_count = final_record['total_sent']
        skipped_count = final_record['total_skipped']
        failed_count = final_record['total_failed']
        failed_list = final_record['failed_list']

        # 统计
        print(f"\n{'='*60}")
        print("发送完成")
        print(f"{'='*60}")
        print(f"成功: {sent_count}")
        print(f"跳过: {skipped_count}")
        print(f"失败: {failed_count}")
        print(f"{'='*60}")

        # 显示失败列表
        if failed_list:
            print(f"\n[失败用户] ({len(failed_list)} 位):")
            for item in failed_list:
                print(f"  - {item['nickname']}: {item.get('reason', '未知错误')}")

        print("\n[提示] 浏览器保持打开30秒...")
        time.sleep(30)

    finally:
        print("\n[完成] 关闭浏览器")
        driver.quit()

if __name__ == "__main__":
    main()
