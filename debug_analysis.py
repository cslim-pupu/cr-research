#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from html_code_analyzer import HTMLCodeAnalyzer

def debug_analysis():
    """调试分析结果"""
    analyzer = HTMLCodeAnalyzer()
    
    # 测试URL
    test_url = "https://mp.weixin.qq.com/s/dzntrjq-ECNdPXl_7jAAew"
    
    print(f"正在分析URL: {test_url}")
    result = analyzer.analyze_html_code(test_url)
    
    print("\n=== 完整分析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 检查关键字段
    print("\n=== 关键字段检查 ===")
    if 'html_analysis' in result:
        print("✓ html_analysis 字段存在")
        html_analysis = result['html_analysis']
        
        for key in ['html_comments', 'meta_tags', 'script_tags', 'css_analysis', 'custom_attributes']:
            if key in html_analysis:
                print(f"✓ {key} 存在: {len(str(html_analysis[key]))} 字符")
            else:
                print(f"✗ {key} 不存在")
    else:
        print("✗ html_analysis 字段不存在")
    
    if 'development_info' in result:
        print("✓ development_info 字段存在")
        dev_info = result['development_info']
        print(f"  开发信息内容: {json.dumps(dev_info, ensure_ascii=False, indent=2)}")
    else:
        print("✗ development_info 字段不存在")

if __name__ == "__main__":
    debug_analysis()