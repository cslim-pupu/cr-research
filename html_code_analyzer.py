#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML源代码版权分析器
功能：分析微信公众号页面的HTML源代码，查找版权信息和代码作者
"""

import requests
import re
import json
import time
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
from typing import Dict, List, Optional, Tuple
import base64

class HTMLCodeAnalyzer:
    """HTML源代码版权分析器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志记录"""
        logger.add("html_code_analyzer.log", rotation="10 MB", level="INFO")
    
    def _init_selenium_driver(self):
        """初始化Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            try:
                self.driver = webdriver.Chrome(
                    service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                logger.info("Selenium WebDriver 初始化成功")
            except Exception as e:
                logger.error(f"Selenium WebDriver 初始化失败: {e}")
                raise
    
    def validate_wechat_url(self, url: str) -> bool:
        """验证是否为有效的微信公众号文章链接"""
        wechat_patterns = [
            r'https://mp\.weixin\.qq\.com/s/',
            r'https://mp\.weixin\.qq\.com/s\?',
        ]
        
        for pattern in wechat_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def fetch_html_source(self, url: str) -> Optional[str]:
        """获取页面的完整HTML源代码"""
        if not self.validate_wechat_url(url):
            logger.error(f"无效的微信公众号文章链接: {url}")
            return None
        
        try:
            # 首先尝试使用requests获取
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            if '请在微信客户端打开链接' in response.text or '该链接已过期' in response.text:
                logger.warning("链接需要在微信客户端打开或已过期，尝试使用Selenium")
                return self._fetch_with_selenium(url)
            
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return self._fetch_with_selenium(url)
    
    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """使用Selenium获取HTML源代码"""
        try:
            self._init_selenium_driver()
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(3)
            
            html_content = self.driver.page_source
            return html_content
            
        except Exception as e:
            logger.error(f"Selenium获取内容失败: {e}")
            return None
    
    def analyze_html_comments(self, html_content: str) -> Dict:
        """分析HTML注释中的版权信息"""
        soup = BeautifulSoup(html_content, 'lxml')
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        
        copyright_info = {
            'html_comments': [],
            'copyright_statements': [],
            'author_mentions': [],
            'creation_info': [],
            'license_info': [],
            'html_attributes': []  # 新增：HTML属性中的版权信息
        }
        
        # 版权相关关键词模式
        copyright_patterns = [
            r'(?i)copyright\s*[©]?\s*([^\n]+)',
            r'(?i)©\s*([^\n]+)',
            r'(?i)author[s]?[：:]\s*([^\n]+)',
            r'(?i)created\s*by[：:]\s*([^\n]+)',
            r'(?i)developed\s*by[：:]\s*([^\n]+)',
            r'(?i)designed\s*by[：:]\s*([^\n]+)',
            r'(?i)coded\s*by[：:]\s*([^\n]+)',
            r'(?i)built\s*by[：:]\s*([^\n]+)',
            r'版权所有[：:]\s*([^\n]+)',
            r'作者[：:]\s*([^\n]+)',
            r'开发者[：:]\s*([^\n]+)',
            r'制作[：:]\s*([^\n]+)',
            # 新增：匹配任何包含版权相关词汇的内容
            r'([^"\s]*(?:copyright|author|creator|developer|designer|coder|builder|owner|holder)[^"\s]*)',
            r'([^"\s]*(?:版权|作者|开发|制作|设计|创建)[^"\s]*)',
            # 匹配简单的名称模式（如 ifsvg, yifu 等）
            r'([a-zA-Z][a-zA-Z0-9_-]{2,20})'
        ]
        
        for comment in comments:
            comment_text = comment.strip()
            if comment_text:
                copyright_info['html_comments'].append(comment_text)
                
                # 检查是否包含版权信息
                for pattern in copyright_patterns:
                    matches = re.findall(pattern, comment_text)
                    if matches:
                        if 'copyright' in pattern.lower() or '©' in pattern:
                            copyright_info['copyright_statements'].extend(matches)
                        elif 'author' in pattern.lower() or '作者' in pattern:
                            copyright_info['author_mentions'].extend(matches)
                        elif any(word in pattern.lower() for word in ['created', 'developed', 'designed', 'coded', 'built', '开发', '制作']):
                            copyright_info['creation_info'].extend(matches)
        
        # 分析HTML标签属性中的版权信息
        all_tags = soup.find_all()
        for tag in all_tags:
            for attr_name, attr_value in tag.attrs.items():
                if isinstance(attr_value, str):
                    # 特殊处理版权相关属性
                    if any(keyword in attr_name.lower() for keyword in ['copyright', 'author', 'creator', 'owner', 'cpy', 'powered-by', 'powered_by']):
                        copyright_info['html_attributes'].append({
                            'tag': tag.name,
                            'attribute': attr_name,
                            'value': attr_value,
                            'matches': [attr_value]
                        })
                        copyright_info['copyright_statements'].append(f"{attr_name}: {attr_value}")
                    
                    # 特殊处理name属性
                    if attr_name.lower() == 'name' and len(attr_value) > 2 and len(attr_value) < 50:
                        copyright_info['html_attributes'].append({
                            'tag': tag.name,
                            'attribute': attr_name,
                            'value': attr_value,
                            'matches': [attr_value]
                        })
                        copyright_info['author_mentions'].append(f"name: {attr_value}")
                    
                    # 检查属性值中是否包含版权信息
                    for pattern in copyright_patterns:
                        matches = re.findall(pattern, attr_value)
                        if matches:
                            copyright_info['html_attributes'].append({
                                'tag': tag.name,
                                'attribute': attr_name,
                                'value': attr_value,
                                'matches': matches
                            })
                            
                            # 分类存储
                            if 'copyright' in pattern.lower() or '©' in pattern:
                                copyright_info['copyright_statements'].extend(matches)
                            elif 'author' in pattern.lower() or '作者' in pattern:
                                copyright_info['author_mentions'].extend(matches)
                            elif any(word in pattern.lower() for word in ['created', 'developed', 'designed', 'coded', 'built', '开发', '制作']):
                                copyright_info['creation_info'].extend(matches)
        
        return copyright_info
    
    def analyze_meta_tags(self, html_content: str) -> Dict:
        """分析HTML meta标签中的版权信息"""
        soup = BeautifulSoup(html_content, 'lxml')
        meta_info = {
            'meta_copyright': [],
            'meta_author': [],
            'meta_generator': [],
            'meta_description': [],
            'meta_keywords': []
        }
        
        # 查找相关的meta标签
        meta_tags = soup.find_all('meta')
        
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if not content:
                continue
            
            # 版权相关的meta标签
            if name in ['copyright', 'rights', 'author', 'creator', 'generator', 'description', 'keywords']:
                if name == 'copyright' or name == 'rights':
                    meta_info['meta_copyright'].append(content)
                elif name == 'author' or name == 'creator':
                    meta_info['meta_author'].append(content)
                elif name == 'generator':
                    meta_info['meta_generator'].append(content)
                elif name == 'description':
                    meta_info['meta_description'].append(content)
                elif name == 'keywords':
                    meta_info['meta_keywords'].append(content)
            
            # Open Graph 标签
            if property_attr.startswith('og:'):
                if 'author' in property_attr or 'creator' in property_attr:
                    meta_info['meta_author'].append(content)
        
        return meta_info
    
    def analyze_script_tags(self, html_content: str) -> Dict:
        """分析JavaScript代码中的版权信息"""
        soup = BeautifulSoup(html_content, 'lxml')
        script_info = {
            'script_comments': [],
            'script_copyright': [],
            'script_author': [],
            'library_info': []
        }
        
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                script_content = script.string
                
                # 查找JavaScript注释中的版权信息
                js_comment_patterns = [
                    r'/\*[\s\S]*?\*/',  # 多行注释
                    r'//.*$'  # 单行注释
                ]
                
                for pattern in js_comment_patterns:
                    comments = re.findall(pattern, script_content, re.MULTILINE)
                    for comment in comments:
                        comment_clean = re.sub(r'[/*]', '', comment).strip()
                        if comment_clean:
                            script_info['script_comments'].append(comment_clean)
                            
                            # 检查版权信息
                            if re.search(r'(?i)copyright|©|author|created|developed', comment_clean):
                                if re.search(r'(?i)copyright|©', comment_clean):
                                    script_info['script_copyright'].append(comment_clean)
                                if re.search(r'(?i)author|created|developed', comment_clean):
                                    script_info['script_author'].append(comment_clean)
                
                # 查找库信息
                library_patterns = [
                    r'(?i)jquery[\s-]?v?([\d.]+)',
                    r'(?i)bootstrap[\s-]?v?([\d.]+)',
                    r'(?i)vue[\s-]?v?([\d.]+)',
                    r'(?i)react[\s-]?v?([\d.]+)',
                    r'(?i)angular[\s-]?v?([\d.]+)'
                ]
                
                for pattern in library_patterns:
                    matches = re.findall(pattern, script_content)
                    if matches:
                        library_name = pattern.split('?')[1].split('[')[0]
                        for version in matches:
                            script_info['library_info'].append(f"{library_name} v{version}")
        
        return script_info
    
    def analyze_css_content(self, html_content: str) -> Dict:
        """分析CSS代码中的版权信息"""
        soup = BeautifulSoup(html_content, 'lxml')
        css_info = {
            'css_comments': [],
            'css_copyright': [],
            'css_author': [],
            'framework_info': []
        }
        
        # 分析内联CSS
        style_tags = soup.find_all('style')
        
        for style in style_tags:
            if style.string:
                css_content = style.string
                
                # 查找CSS注释
                css_comments = re.findall(r'/\*[\s\S]*?\*/', css_content)
                
                for comment in css_comments:
                    comment_clean = re.sub(r'[/*]', '', comment).strip()
                    if comment_clean:
                        css_info['css_comments'].append(comment_clean)
                        
                        # 检查版权信息
                        if re.search(r'(?i)copyright|©|author|created|developed', comment_clean):
                            if re.search(r'(?i)copyright|©', comment_clean):
                                css_info['css_copyright'].append(comment_clean)
                            if re.search(r'(?i)author|created|developed', comment_clean):
                                css_info['css_author'].append(comment_clean)
        
        # 分析外部CSS链接
        link_tags = soup.find_all('link', rel='stylesheet')
        for link in link_tags:
            href = link.get('href', '')
            if href:
                # 检查是否是知名框架
                if 'bootstrap' in href.lower():
                    css_info['framework_info'].append('Bootstrap CSS Framework')
                elif 'fontawesome' in href.lower():
                    css_info['framework_info'].append('Font Awesome Icons')
                elif 'jquery' in href.lower():
                    css_info['framework_info'].append('jQuery UI CSS')
        
        return css_info
    
    def extract_embedded_data(self, html_content: str) -> Dict:
        """提取嵌入的数据和配置信息"""
        soup = BeautifulSoup(html_content, 'lxml')
        embedded_info = {
            'json_data': [],
            'config_data': [],
            'api_endpoints': [],
            'tracking_codes': []
        }
        
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                script_content = script.string
                
                # 查找JSON数据
                try:
                    # 查找可能的JSON配置
                    json_patterns = [
                        r'var\s+\w+\s*=\s*(\{[^}]+\})',
                        r'window\.[\w.]+\s*=\s*(\{[^}]+\})',
                        r'config\s*[=:]\s*(\{[^}]+\})'
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, script_content)
                        for match in matches:
                            try:
                                # 尝试解析JSON
                                json_obj = json.loads(match)
                                embedded_info['json_data'].append(match)
                            except:
                                # 如果不是有效JSON，仍然记录
                                embedded_info['config_data'].append(match)
                
                except Exception as e:
                    logger.debug(f"JSON解析错误: {e}")
                
                # 查找API端点
                api_patterns = [
                    r'(?i)api[/\w]*',
                    r'https?://[\w.-]+/api[/\w]*',
                    r'/[\w/]*api[/\w]*'
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, script_content)
                    embedded_info['api_endpoints'].extend(matches)
                
                # 查找跟踪代码
                tracking_patterns = [
                    r'(?i)google-analytics',
                    r'(?i)gtag\(',
                    r'(?i)_gaq',
                    r'(?i)baidu.*tongji',
                    r'(?i)cnzz'
                ]
                
                for pattern in tracking_patterns:
                    if re.search(pattern, script_content):
                        embedded_info['tracking_codes'].append(pattern)
        
        return embedded_info
    
    def identify_development_info(self, all_analysis: Dict) -> Dict:
        """综合分析识别开发信息"""
        dev_info = {
            'primary_author': None,
            'all_authors': [],
            'copyright_holders': [],
            'development_tools': [],
            'frameworks_used': [],
            'creation_date': None,
            'confidence_score': 0.0
        }
        
        # 收集所有作者信息
        authors = []
        
        # 从HTML注释中提取
        if 'html_comments' in all_analysis:
            authors.extend(all_analysis['html_comments'].get('author_mentions', []))
            authors.extend(all_analysis['html_comments'].get('creation_info', []))
        
        # 从meta标签中提取
        if 'meta_tags' in all_analysis:
            authors.extend(all_analysis['meta_tags'].get('meta_author', []))
        
        # 从脚本中提取
        if 'script_tags' in all_analysis:
            authors.extend(all_analysis['script_tags'].get('script_author', []))
        
        # 从CSS中提取
        if 'css_content' in all_analysis:
            authors.extend(all_analysis['css_content'].get('css_author', []))
        
        # 去重和清理
        unique_authors = list(set([author.strip() for author in authors if author.strip()]))
        dev_info['all_authors'] = unique_authors
        
        # 确定主要作者（选择最常出现的）
        if unique_authors:
            author_counts = {}
            for author in authors:
                author = author.strip()
                if author:
                    author_counts[author] = author_counts.get(author, 0) + 1
            
            if author_counts:
                primary_author = max(author_counts, key=author_counts.get)
                dev_info['primary_author'] = {
                    'name': primary_author,
                    'confidence': author_counts[primary_author] / len(authors),
                    'source': 'multiple_sources'
                }
        
        # 收集版权持有者
        copyright_holders = []
        for analysis_type in all_analysis.values():
            if isinstance(analysis_type, dict):
                copyright_holders.extend(analysis_type.get('copyright_statements', []))
                copyright_holders.extend(analysis_type.get('script_copyright', []))
                copyright_holders.extend(analysis_type.get('css_copyright', []))
                copyright_holders.extend(analysis_type.get('meta_copyright', []))
        
        dev_info['copyright_holders'] = list(set([holder.strip() for holder in copyright_holders if holder.strip()]))
        
        # 收集开发工具和框架
        frameworks = []
        if 'script_tags' in all_analysis:
            frameworks.extend(all_analysis['script_tags'].get('library_info', []))
        if 'css_content' in all_analysis:
            frameworks.extend(all_analysis['css_content'].get('framework_info', []))
        if 'meta_tags' in all_analysis:
            frameworks.extend(all_analysis['meta_tags'].get('meta_generator', []))
        
        dev_info['frameworks_used'] = list(set(frameworks))
        
        # 计算置信度
        confidence_factors = [
            len(dev_info['all_authors']) > 0,
            len(dev_info['copyright_holders']) > 0,
            dev_info['primary_author'] is not None,
            len(dev_info['frameworks_used']) > 0
        ]
        
        dev_info['confidence_score'] = sum(confidence_factors) / len(confidence_factors)
        
        return dev_info
    
    def analyze_html_code(self, url: str) -> Dict:
        """分析HTML源代码的完整流程"""
        logger.info(f"开始分析HTML源代码: {url}")
        
        # 获取HTML源代码
        html_content = self.fetch_html_source(url)
        if not html_content:
            return {'error': '无法获取HTML源代码'}
        
        # 执行各种分析
        html_comments = self.analyze_html_comments(html_content)
        meta_tags = self.analyze_meta_tags(html_content)
        script_tags = self.analyze_script_tags(html_content)
        css_content = self.analyze_css_content(html_content)
        embedded_data = self.extract_embedded_data(html_content)
        
        all_analysis = {
            'html_comments': html_comments,
            'meta_tags': meta_tags,
            'script_tags': script_tags,
            'css_content': css_content,
            'embedded_data': embedded_data
        }
        
        # 综合分析开发信息
        development_info = self.identify_development_info(all_analysis)
        
        result = {
            'url': url,
            'analysis_type': 'html_source_code',
            'html_analysis': all_analysis,
            'development_info': development_info,
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'html_size': len(html_content)
        }
        
        logger.info(f"HTML源代码分析完成")
        return result
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()

def main():
    """主函数 - 命令行接口"""
    import sys
    
    if len(sys.argv) != 2:
        print("使用方法: python html_code_analyzer.py <微信文章链接>")
        sys.exit(1)
    
    url = sys.argv[1]
    analyzer = HTMLCodeAnalyzer()
    
    try:
        result = analyzer.analyze_html_code(url)
        
        if 'error' in result:
            print(f"错误: {result['error']}")
            sys.exit(1)
        
        # 输出结果
        print("\n=== HTML源代码分析结果 ===")
        print(f"URL: {result['url']}")
        print(f"HTML大小: {result['html_size']} 字符")
        
        print("\n=== 开发信息 ===")
        dev_info = result['development_info']
        
        if dev_info['primary_author']:
            author = dev_info['primary_author']
            print(f"主要作者: {author['name']} (置信度: {author['confidence']:.2f})")
        
        if dev_info['all_authors']:
            print(f"所有作者: {', '.join(dev_info['all_authors'])}")
        
        if dev_info['copyright_holders']:
            print(f"版权持有者: {', '.join(dev_info['copyright_holders'])}")
        
        if dev_info['frameworks_used']:
            print(f"使用的框架/库: {', '.join(dev_info['frameworks_used'])}")
        
        print(f"\n整体置信度: {dev_info['confidence_score']:.2f}")
        print(f"分析时间: {result['analysis_time']}")
        
    except Exception as e:
        logger.error(f"分析过程中出现错误: {e}")
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()