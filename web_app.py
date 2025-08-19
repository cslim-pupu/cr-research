#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章版权分析器 - Web界面
使用Flask提供简单的Web界面
"""

from flask import Flask, render_template, request, jsonify
from html_code_analyzer import HTMLCodeAnalyzer
from loguru import logger
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 初始化HTML源代码分析器
html_analyzer = HTMLCodeAnalyzer()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """分析文章接口"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': '请提供有效的URL'})
        
        # 只使用HTML源代码分析器
        result = html_analyzer.analyze_html_code(url)
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"分析过程中出现错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    """健康检查接口"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # 创建模板目录
    os.makedirs('templates', exist_ok=True)
    
    # 从环境变量获取端口，默认为8080（用于本地开发）
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)