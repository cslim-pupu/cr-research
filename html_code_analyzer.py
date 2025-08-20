#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML代码分析器
用于分析网页的HTML源代码，提取开发信息、版权信息等
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
    """HTML代码分析器类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        logger.add("html_analyzer.log", rotation="10 MB", level="INFO")
    
    def _init_selenium_driver(self):
        """初始化Selenium WebDriver"""
        if self.driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-plugins')
                chrome_options.add_argument('--disable-images')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--remote-debugging-port=9222')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                chrome_options.add_argument('--disable-renderer-backgrounding')
                chrome_options.add_argument('--disable-features=TranslateUI')
                chrome_options.add_argument('--disable-ipc-flooding-protection')
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                
                # 检查是否在云环境中运行
                import os
                if os.environ.get('RENDER') or os.environ.get('DYNO') or os.path.exists('/usr/bin/google-chrome-stable'):
                    # Docker/云环境配置
                    chrome_options.binary_location = '/usr/bin/google-chrome-stable'
                    chrome_options.add_argument('--single-process')
                    chrome_options.add_argument('--disable-web-security')
                    chrome_options.add_argument('--allow-running-insecure-content')
                    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
                
                self.driver = webdriver.Chrome(
                    service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                logger.info("Selenium WebDriver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Selenium WebDriver: {e}")
                self.driver = None
    
    def validate_wechat_url(self, url: str) -> bool:
        """验证是否为微信公众号文章URL"""
        wechat_patterns = [
            r'mp\.weixin\.qq\.com',
            r'weixin\.qq\.com'
        ]
        
        for pattern in wechat_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def fetch_html_source(self, url: str) -> Optional[str]:
        """获取网页HTML源代码"""
        try:
            # 首先尝试使用requests
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 对于微信文章，优先使用requests，因为它们的内容是服务端渲染的
            if self.validate_wechat_url(url):
                logger.info("WeChat article detected, using requests (server-side rendered)")
                return response.text
            
            # 对于其他需要JavaScript的页面，才使用Selenium
            if 'javascript' in response.text.lower() and len(response.text) < 1000:
                logger.info("Detected minimal content, trying Selenium")
                return self._fetch_with_selenium(url)
            
            return response.text
            
        except Exception as e:
            logger.warning(f"Failed to fetch with requests: {e}, trying Selenium")
            return self._fetch_with_selenium(url)
    
    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """使用Selenium获取网页内容"""
        try:
            self._init_selenium_driver()
            if self.driver is None:
                return None
            
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待页面完全加载
            time.sleep(3)
            
            return self.driver.page_source
            
        except Exception as e:
            logger.error(f"Failed to fetch with Selenium: {e}")
            return None
    
    def analyze_html_comments(self, html_content: str) -> Dict:
        """分析HTML注释"""
        soup = BeautifulSoup(html_content, 'lxml')
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        
        comment_analysis = {
            'total_comments': len(comments),
            'comments': []
        }
        
        for comment in comments:
            comment_text = comment.strip()
            if comment_text:
                comment_analysis['comments'].append({
                    'content': comment_text,
                    'length': len(comment_text)
                })
        
        return {
            'html_comments': comment_analysis
        }
    
    def analyze_meta_tags(self, html_content: str) -> Dict:
        """分析Meta标签"""
        soup = BeautifulSoup(html_content, 'lxml')
        meta_tags = soup.find_all('meta')
        
        meta_analysis = {
            'total_meta_tags': len(meta_tags),
            'meta_tags': []
        }
        
        for meta in meta_tags:
            meta_info = {}
            
            # 获取所有属性
            for attr, value in meta.attrs.items():
                if isinstance(value, list):
                    meta_info[attr] = ' '.join(value)
                else:
                    meta_info[attr] = value
            
            if meta_info:  # 只添加非空的meta标签
                meta_analysis['meta_tags'].append(meta_info)
        
        return {
            'meta_tags': meta_analysis
        }
    
    def analyze_script_tags(self, html_content: str) -> Dict:
        """分析Script标签"""
        soup = BeautifulSoup(html_content, 'lxml')
        script_tags = soup.find_all('script')
        
        script_analysis = {
            'total_script_tags': len(script_tags),
            'external_scripts': [],
            'inline_scripts_count': 0,
            'script_libraries': []
        }
        
        for script in script_tags:
            if script.get('src'):
                src = script.get('src')
                script_analysis['external_scripts'].append(src)
                
                # 识别常见的JavaScript库
                libraries = {
                    'jquery': r'jquery',
                    'bootstrap': r'bootstrap',
                    'vue': r'vue',
                    'react': r'react',
                    'angular': r'angular',
                    'lodash': r'lodash',
                    'moment': r'moment',
                    'axios': r'axios'
                }
                
                for lib_name, pattern in libraries.items():
                    if re.search(pattern, src.lower()):
                        if lib_name not in script_analysis['script_libraries']:
                            script_analysis['script_libraries'].append(lib_name)
            else:
                script_analysis['inline_scripts_count'] += 1
        
        return {
            'script_tags': script_analysis
        }
    
    def analyze_css_content(self, html_content: str) -> Dict:
        """分析CSS内容"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 分析外部CSS文件
        link_tags = soup.find_all('link', {'rel': 'stylesheet'})
        external_css = [link.get('href') for link in link_tags if link.get('href')]
        
        # 分析内联CSS
        style_tags = soup.find_all('style')
        inline_css_count = len(style_tags)
        
        css_analysis = {
            'external_css_count': len(external_css),
            'external_css_files': external_css,
            'inline_css_count': inline_css_count,
            'css_frameworks': []
        }
        
        # 识别CSS框架
        all_css_content = ' '.join([link.get('href', '') for link in link_tags])
        frameworks = {
            'bootstrap': r'bootstrap',
            'foundation': r'foundation',
            'bulma': r'bulma',
            'tailwind': r'tailwind',
            'materialize': r'materialize'
        }
        
        for framework, pattern in frameworks.items():
            if re.search(pattern, all_css_content.lower()):
                css_analysis['css_frameworks'].append(framework)
        
        return {
            'css_analysis': css_analysis
        }
    
    def extract_embedded_data(self, html_content: str) -> Dict:
        """提取嵌入的数据"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        embedded_data = {
            'json_ld': [],
            'microdata': [],
            'data_attributes': []
        }
        
        # 提取JSON-LD数据
        json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_ld_scripts:
            try:
                if script.string:
                    json_data = json.loads(script.string)
                    embedded_data['json_ld'].append(json_data)
            except json.JSONDecodeError:
                continue
        
        # 提取微数据
        microdata_elements = soup.find_all(attrs={'itemscope': True})
        for element in microdata_elements:
            microdata_info = {
                'itemtype': element.get('itemtype'),
                'itemscope': element.get('itemscope'),
                'tag': element.name
            }
            embedded_data['microdata'].append(microdata_info)
        
        # 提取data-*属性
        all_elements = soup.find_all()
        data_attrs = set()
        for element in all_elements:
            for attr in element.attrs:
                if attr.startswith('data-'):
                    data_attrs.add(attr)
        
        embedded_data['data_attributes'] = list(data_attrs)
        
        return {
            'embedded_data': embedded_data
        }
    
    def analyze_custom_attributes(self, html_content: str) -> Dict:
        """分析HTML元素的自定义属性，特别是版权相关属性"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        custom_attrs = {
            'copyright_attributes': [],
            'labels_attributes': [],
            'other_custom_attributes': []
        }
        
        # 查找所有元素的属性
        all_elements = soup.find_all()
        
        for elem in all_elements:
            if elem.attrs:
                # 查找版权相关属性
                copyright_attrs = ['copyright', 'data-copyright', 'powered-by', 'data-powered-by']
                for attr_name in copyright_attrs:
                    if attr_name in elem.attrs:
                        attr_value = elem.get(attr_name)
                        if attr_value:
                            custom_attrs['copyright_attributes'].append({
                                'tag': elem.name,
                                'attribute': attr_name,
                                'copyright': attr_value
                            })
                
                # 查找作者/名称相关属性
                name_attrs = ['name', 'author', 'data-author', 'data-name']
                for attr_name in name_attrs:
                    if attr_name in elem.attrs:
                        attr_value = elem.get(attr_name)
                        if attr_value and len(attr_value) > 2:  # 过滤掉太短的值
                            custom_attrs['labels_attributes'].append({
                                'tag': elem.name,
                                'attribute': attr_name,
                                'labels': attr_value
                            })
                
                # 查找其他可能包含版权信息的属性
                for attr_name, attr_value in elem.attrs.items():
                    if isinstance(attr_value, str) and any(keyword in attr_value.lower() for keyword in ['版权', 'copyright', '©']):
                        custom_attrs['other_custom_attributes'].append({
                            'tag': elem.name,
                            'attribute': attr_name,
                            'value': attr_value
                        })
        
        return {
            'custom_attributes': custom_attrs
        }
    
    def identify_development_info(self, all_analysis: Dict) -> Dict:
        """识别开发相关信息和版权信息"""
        # 收集所有作者和版权信息
        all_authors = set()
        copyright_holders = set()
        frameworks_used = set()
        
        # HTML注释分析已移除
        
        # 从Meta标签中提取
        if 'meta_tags' in all_analysis:
            meta_info = all_analysis['meta_tags']
            if 'meta_tags' in meta_info:  # 获取实际的meta标签列表
                for meta in meta_info['meta_tags']:
                    # 检查author相关属性
                    if 'name' in meta and meta['name'].lower() in ['author', 'creator']:
                        if 'content' in meta:
                            all_authors.add(meta['content'])
                    # 检查copyright相关属性
                    if 'name' in meta and 'copyright' in meta['name'].lower():
                        if 'content' in meta:
                            copyright_holders.add(meta['content'])
                    # 检查property属性
                    if 'property' in meta:
                        prop = meta['property'].lower()
                        if 'author' in prop and 'content' in meta:
                            all_authors.add(meta['content'])
                        elif 'copyright' in prop and 'content' in meta:
                            copyright_holders.add(meta['content'])
        
        # 从脚本标签中提取框架信息
        if 'script_tags' in all_analysis:
            script_info = all_analysis['script_tags']
            if 'script_libraries' in script_info:
                frameworks_used.update(script_info['script_libraries'])
        
        # 从CSS分析中提取框架信息
        if 'css_analysis' in all_analysis:
            css_info = all_analysis['css_analysis']
            if 'css_frameworks' in css_info:
                frameworks_used.update(css_info['css_frameworks'])
        
        # 从自定义属性中提取
        if 'custom_attributes' in all_analysis:
            custom_attrs = all_analysis['custom_attributes']
            if 'copyright_attributes' in custom_attrs:
                for attr in custom_attrs['copyright_attributes']:
                    if isinstance(attr, dict) and 'copyright' in attr:
                        copyright_holders.add(attr['copyright'])
            if 'labels_attributes' in custom_attrs:
                for attr in custom_attrs['labels_attributes']:
                    if isinstance(attr, dict) and 'labels' in attr:
                        all_authors.add(attr['labels'])
        
        # 转换为列表并过滤空值
        all_authors_list = [author for author in all_authors if author and author.strip()]
        copyright_holders_list = [holder for holder in copyright_holders if holder and holder.strip()]
        frameworks_used_list = [framework for framework in frameworks_used if framework and framework.strip()]
        
        # 确定主要作者（选择最常见或最可信的）
        primary_author = None
        confidence = 0.0
        
        if all_authors_list:
            # 简单选择第一个作者作为主要作者
            primary_author = {
                'name': all_authors_list[0],
                'confidence': 0.8 if len(all_authors_list) == 1 else 0.6
            }
            confidence = primary_author['confidence']
        
        # 计算整体置信度
        confidence_factors = []
        if all_authors_list:
            confidence_factors.append(0.4)
        if copyright_holders_list:
            confidence_factors.append(0.3)
        if frameworks_used_list:
            confidence_factors.append(0.2)
        
        overall_confidence = sum(confidence_factors) if confidence_factors else 0.0
        
        return {
            'development_info': {
                'primary_author': primary_author,
                'all_authors': all_authors_list,
                'copyright_holders': copyright_holders_list,
                'frameworks_used': frameworks_used_list,
                'confidence_score': overall_confidence
            }
        }
    
    def extract_wechat_article_info(self, html_content: str, url: str) -> Dict:
        """提取微信公众号文章基本信息"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 提取文章标题
        title = "未找到标题"
        title_selectors = [
            'h1#activity-name',
            '.rich_media_title',
            'h1',
            'title'
        ]
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                break
        
        # 提取发布时间
        publish_time = "未找到发布时间"
        time_selectors = [
            '#publish_time',
            '.rich_media_meta_text',
            '[data-time]',
            '.time'
        ]
        for selector in time_selectors:
            element = soup.select_one(selector)
            if element:
                publish_time = element.get_text().strip()
                break
        
        # 从脚本中提取发布时间（改进的正则表达式）
        if publish_time == "未找到发布时间":
            # 搜索 var createTime 格式
            create_time_match = re.search(r"var createTime = ['\"]([^'\"]*)['\"];", html_content)
            if create_time_match:
                publish_time = create_time_match.group(1)
            else:
                # 直接在HTML文本中搜索时间戳格式
                time_match = re.search(r'var publish_time = (\d{10})', html_content)
                if time_match:
                    timestamp = int(time_match.group(1))
                    publish_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                else:
                    # 尝试其他时间格式
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', html_content)
                    if date_match:
                        publish_time = date_match.group(1)
        
        # 提取公众号名称
        account_name = "未找到公众号名称"
        name_selectors = [
            '#js_name',
            '.rich_media_meta_nickname',
            '.account_nickname',
            '.profile_nickname'
        ]
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                account_name = element.get_text().strip()
                break
        
        # 从脚本中提取标题和公众号名称（使用正则表达式）
        if title == "未找到标题" or account_name == "未找到公众号名称":
            # 直接在HTML文本中搜索JavaScript变量
            # 提取标题
            if title == "未找到标题":
                title_match = re.search(r'var msg_title = ([^;]+);', html_content)
                if title_match:
                    title_value = title_match.group(1).strip()
                    # 处理格式如 '标题'.html(false)
                    if title_value.startswith("'") and "'.html(false)" in title_value:
                        title = title_value.split("'")[1]
                    elif title_value.startswith('"') and '".html(false)' in title_value:
                        title = title_value.split('"')[1]
            
            # 提取公众号名称
            if account_name == "未找到公众号名称":
                nickname_match = re.search(r'var nickname = ([^;]+);', html_content)
                if nickname_match:
                    nickname_value = nickname_match.group(1).strip()
                    # 处理格式如 htmlDecode("公众号名称")
                    if 'htmlDecode(' in nickname_value:
                        decode_match = re.search(r'htmlDecode\(["\']([^"\']*)["\'\])', nickname_value)
                        if decode_match:
                            account_name = decode_match.group(1)
        
        # 提取原始链接（通常就是当前URL）
        original_url = url
        
        # 尝试从页面中提取规范链接
        canonical_link = soup.find('link', {'rel': 'canonical'})
        if canonical_link and canonical_link.get('href'):
            original_url = canonical_link.get('href')
        
        return {
            'title': title,
            'publish_time': publish_time,
            'account_name': account_name,
            'original_url': original_url
        }
    
    def analyze_html_code(self, url: str) -> Dict:
        """分析HTML源代码的完整流程"""
        try:
            logger.info(f"Starting analysis for URL: {url}")
            
            # 获取HTML源代码
            html_content = self.fetch_html_source(url)
            if not html_content:
                return {
                    'error': '无法获取网页内容',
                    'url': url,
                    'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # 执行各种分析
            all_analysis = {}
            # HTML注释分析已移除
            all_analysis.update(self.analyze_meta_tags(html_content))
            all_analysis.update(self.analyze_script_tags(html_content))
            all_analysis.update(self.analyze_css_content(html_content))
            all_analysis.update(self.extract_embedded_data(html_content))
            all_analysis.update(self.analyze_custom_attributes(html_content))
            
            # 识别开发信息
            dev_info = self.identify_development_info(all_analysis)
            all_analysis.update(dev_info)
            
            # 如果是微信文章，提取文章信息
            wechat_info = {}
            if self.validate_wechat_url(url):
                wechat_info = self.extract_wechat_article_info(html_content, url)
            
            # 将development_info提升到根级别以便前端访问
            result = {
                'url': url,
                'analysis_type': 'HTML源代码分析',
                'html_analysis': all_analysis,
                'wechat_article_info': wechat_info,
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'html_size': len(html_content)
            }
            
            # 如果有开发信息，将其提升到根级别
            if 'development_info' in all_analysis:
                result['development_info'] = all_analysis['development_info']
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {url}: {e}")
            return {
                'error': f'分析失败: {str(e)}',
                'url': url,
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()

def main():
    """主函数，用于测试"""
    analyzer = HTMLCodeAnalyzer()
    
    # 测试URL
    test_urls = [
        "https://mp.weixin.qq.com/s/example",  # 微信文章示例
        "https://www.example.com"  # 普通网站示例
    ]
    
    for url in test_urls:
        print(f"\n分析URL: {url}")
        result = analyzer.analyze_html_code(url)
        
        if 'error' in result:
            print(f"错误: {result['error']}")
        else:
            print(f"分析类型: {result['analysis_type']}")
            print(f"HTML大小: {result['html_size']} 字符")
            print(f"分析时间: {result['analysis_time']}")
            
            if result.get('wechat_article_info'):
                wechat_info = result['wechat_article_info']
                print(f"文章标题: {wechat_info.get('title', 'N/A')}")
                print(f"发布时间: {wechat_info.get('publish_time', 'N/A')}")
                print(f"公众号名称: {wechat_info.get('account_name', 'N/A')}")
                print(f"原始链接: {wechat_info.get('original_url', 'N/A')}")

if __name__ == "__main__":
    main()