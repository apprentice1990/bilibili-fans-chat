# 归档文件说明

本目录包含项目开发过程中的测试脚本、调试脚本和旧版本文件。

## 文件分类

### 测试脚本 (test_*.py)
- test_batch_send.py - 批量发送测试
- test_check_textarea.py - 文本框测试
- test_complete_flow.py - 完整流程测试
- test_direct_url.py - 直接URL测试
- test_fetch.py - 抓取测试
- test_multiple_users.py - 多用户测试
- test_real_send.py - 真实发送测试
- test_selenium_keys.py - Selenium按键测试
- test_send_multiple.py - 多条发送测试
- test_send_one.py - 单条发送测试
- test_send_single.py - 单条发送测试
- test_send_verify.py - 发送验证测试

### 调试脚本 (debug_*.py, probe_*.py)
- debug_page.py - 页面调试
- debug_users.py - 用户调试
- debug_video_page.py - 视频页面调试
- probe_comments_area.py - 评论区探测
- probe_page_structure.py - 页面结构探测

### 旧版本脚本
- batch_send_workable.py - 批量发送可用版本
- bilibili_msg_sender.py - 旧版消息发送器
- bv_to_aid.py - BV转AV工具
- close_popup_and_send.py - 关闭弹窗并发送
- comment_fetcher.py - 评论爬取器
- rate_limiter.py - 速率限制器
- manual_send.py - 手动发送

### 实验性脚本 (fetch_*.py)
以下脚本是在开发过程中尝试的不同方法：

#### DOM爬取方法
- fetch_all_comments.py - 完整评论获取
- fetch_all_comments_api_improved.py - 改进的API获取
- fetch_all_comments_selenium.py - Selenium爬取
- fetch_comments_crawler.py - 爬虫方式
- fetch_comments_dynamic.py - 动态加载爬取
- fetch_comments_aggressive.py - 激进爬取

#### 网络监听方法
- fetch_comments_network.py - 网络请求监听
- fetch_comments_paginator.py - 分页网络请求

#### Playwright方法
- fetch_comments_playwright.py - Playwright爬虫

#### API方法
- fetch_comments_api_pagination.py - API分页获取
- fetch_via_api.py - 通过API获取

#### 其他
- fetch_all_replies.py - 抓取所有回复（早期版本）

### 其他脚本
- final_complete_send.py - 完整发送（最终版）
- final_send_test.py - 最终发送测试

## 说明

这些文件是开发过程中产生的，用于测试和验证不同的实现方法。

**当前使用的核心文件（在主目录）：**
- `run_campaign.py` - 整合流程脚本（推荐使用）
- `fetch_all_replies_complete.py` - 最终版评论抓取
- `batch_send.py` - 最终版批量发送
- `msg_config.py` - 配置文件
- `config.example.py` - 配置示例

## 开发历史

这个项目经历了多次迭代：

1. **早期尝试**：使用DOM爬取，只能获取7个用户
2. **网络监听**：尝试监听网络请求，获取19个用户
3. **API发现**：发现API返回子回复，成功获取61个用户
4. **最终方案**：`fetch_all_replies_complete.py` - 完整获取主评论+所有子回复

详见主目录的README.md了解最终使用方法。
