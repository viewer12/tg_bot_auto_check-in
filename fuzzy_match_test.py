#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re

# 设置日志格式
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def fuzzy_text_match(text1, text2):
    """
    实现模糊文本匹配，忽略大小写、空格、标点符号和表情符号前后的差异
    
    Args:
        text1: 第一个文本字符串
        text2: 第二个文本字符串
    
    Returns:
        bool: 如果两个字符串模糊匹配则返回True
    """
    if not text1 or not text2:
        return False
    
    # 原始文本记录
    original_text1 = text1
    original_text2 = text2
    
    # 将两个字符串都转为小写
    text1 = text1.lower()
    text2 = text2.lower()
    
    # 去除常见标点符号和空白
    pattern = r'[\s.,，。:：;；!！?？_\-—～~()]'
    text1 = re.sub(pattern, '', text1)
    text2 = re.sub(pattern, '', text2)
    
    # 清除表情符号和其他特殊字符
    emoji_pattern = r'[\U00010000-\U0010ffff]'
    text1 = re.sub(emoji_pattern, '', text1, flags=re.UNICODE)
    text2 = re.sub(emoji_pattern, '', text2, flags=re.UNICODE)
    
    # 基础检查：一个字符串是否包含在另一个字符串中
    base_match = text1 in text2 or text2 in text1
    
    # 如果基础检查失败，进行关键词匹配
    if not base_match:
        # 签到关键词匹配
        checkin_keywords = ["签到", "打卡", "checkin", "check", "签", "到"]
        
        # 提取文本中的关键词
        text1_keywords = [kw for kw in checkin_keywords if kw in text1]
        text2_keywords = [kw for kw in checkin_keywords if kw in text2]
        
        # 如果两边都有共同的签到关键词，认为匹配成功
        keyword_match = bool(set(text1_keywords) & set(text2_keywords))
        
        result = keyword_match
    else:
        result = base_match
    
    if result:
        print(f"模糊匹配成功: '{original_text1}' 与 '{original_text2}'")
        print(f"  处理后: '{text1}' 与 '{text2}'")
    else:
        print(f"模糊匹配失败: '{original_text1}' 与 '{original_text2}'")
        print(f"  处理后: '{text1}' 与 '{text2}'")
    
    return result

def test_fuzzy_match():
    """测试模糊匹配功能"""
    print("开始测试模糊匹配功能...")
    
    test_cases = [
        # 按钮定义, 按钮实际文本, 预期结果
        ("签到", "🎯 签到", True),
        ("签到", "每日签到", True),
        ("签到", "签 到", True),
        ("签到", "签.到", True),
        ("签到", "点击签到", True),
        ("签到", "登录", False),
        ("check in", "Check-In", True),
        ("check in", "Daily Check In", True),
        ("check in", "登录", False),
        ("签  到", "🎯 签到", True),
        ("每日签到", "🎯 签到", True),
        ("打卡", "签到打卡", True),
        ("打卡", "打卡签到", True),
        ("打卡", "每日打卡", True),
    ]
    
    for i, (button_def, button_text, expected) in enumerate(test_cases):
        print(f"\n测试案例 {i+1}:")
        result = fuzzy_text_match(button_def, button_text)
        if result == expected:
            print(f"✅ 测试通过: '{button_def}' 与 '{button_text}' {'匹配' if expected else '不匹配'}")
        else:
            print(f"❌ 测试失败: '{button_def}' 与 '{button_text}' {'应该匹配' if expected else '不应该匹配'}")
    
    print("\n模糊匹配功能测试完成")

if __name__ == "__main__":
    test_fuzzy_match() 