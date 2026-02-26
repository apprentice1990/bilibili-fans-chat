#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速率限制器
用于控制私信发送速率，避免触发B站风控
"""

import time
import random
from datetime import datetime
from msg_config import (
    MIN_INTERVAL,
    MAX_INTERVAL,
    BATCH_SIZE,
    BATCH_PAUSE,
    MAX_SENDS_PER_HOUR
)


class RateLimiter:
    """速率限制器 - 保守模式"""

    def __init__(self):
        """初始化速率限制器"""
        self.last_send_time = None
        self.send_count = 0
        self.batch_count = 0
        self.start_time = time.time()

    def wait_if_needed(self):
        """
        根据速率限制等待

        保守模式策略：
        1. 基础间隔：30-90秒随机
        2. 批次暂停：每10条暂停5分钟
        3. 每小时上限：20条
        """
        now = time.time()

        # 1. 检查基础间隔
        if self.last_send_time:
            elapsed = now - self.last_send_time
            min_interval = random.randint(MIN_INTERVAL, MAX_INTERVAL)

            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                print(f"[等待] 距离上次发送仅{elapsed:.1f}秒，等待{wait_time:.1f}秒...")
                time.sleep(wait_time)

        # 2. 检查批次暂停
        self.batch_count += 1
        if self.batch_count >= BATCH_SIZE:
            print(f"\n{'='*60}")
            print(f"[批次暂停] 已发送{BATCH_SIZE}条，暂停{BATCH_PAUSE//60}分钟...")
            print(f"{'='*60}\n")

            for i in range(BATCH_PAUSE, 0, -60):
                minutes = i // 60
                print(f"[倒计时] 剩余 {minutes} 分钟...", end='\r')
                time.sleep(60)

            print()  # 换行
            self.batch_count = 0

        # 3. 检查每小时限制
        self.send_count += 1
        elapsed_hour = (now - self.start_time) / 3600

        if elapsed_hour > 0:
            current_rate = self.send_count / elapsed_hour
            if current_rate > MAX_SENDS_PER_HOUR:
                # 已超过每小时限制，等待到下一小时
                print(f"\n[警告] 当前发送速率已超过{MAX_SENDS_PER_HOUR}条/小时")
                print(f"[等待] 等待到下一小时...")

                # 计算到下一小时的等待时间
                wait_to_hour = 3600 - (now % 3600)
                time.sleep(wait_to_hour)

                # 重置计数器
                self.send_count = 0
                self.start_time = time.time()

        self.last_send_time = time.time()

    def get_stats(self):
        """
        获取统计信息

        返回:
            dict: 包含发送数量、运行时间、平均速率等统计信息
        """
        now = time.time()
        elapsed_total = now - self.start_time
        elapsed_hour = elapsed_total / 3600

        if elapsed_hour > 0:
            avg_rate_per_hour = self.send_count / elapsed_hour
        else:
            avg_rate_per_hour = 0

        return {
            "total_sent": self.send_count,
            "batch_sent": self.batch_count,
            "elapsed_seconds": int(elapsed_total),
            "elapsed_minutes": int(elapsed_total / 60),
            "elapsed_hours": elapsed_hour,
            "avg_rate_per_hour": avg_rate_per_hour,
            "last_send_time": datetime.fromtimestamp(self.last_send_time).isoformat() if self.last_send_time else None,
        }

    def reset(self):
        """重置计数器"""
        self.last_send_time = None
        self.send_count = 0
        self.batch_count = 0
        self.start_time = time.time()


if __name__ == "__main__":
    # 测试代码
    print("速率限制器测试")
    print("="*60)

    limiter = RateLimiter()

    # 模拟发送5条（每条等待时间较短，仅用于演示）
    for i in range(5):
        print(f"\n[发送] 第 {i+1} 条")
        limiter.wait_if_needed()
        print(f"[完成] 已发送 {i+1} 条")

    # 显示统计
    print(f"\n{'='*60}")
    print("统计信息")
    print(f"{'='*60}")
    stats = limiter.get_stats()
    print(f"总计发送: {stats['total_sent']} 条")
    print(f"运行时间: {stats['elapsed_minutes']} 分钟")
    print(f"平均速率: {stats['avg_rate_per_hour']:.2f} 条/小时")
