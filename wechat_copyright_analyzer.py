#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章版权信息分析器
功能：通过公众号文章链接分析版权信息并识别作者
"""

import requests
import re
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
import jieba
# from fuzzywuzzy import fuzz  # 移除依赖
from typing import Dict, List, Optional, Tuple

class WeChatCopyrightAnalyzer:
    """微信公众号文章版权信息分析器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志记录"""
        logger.add("copyright_analyzer.log", rotation="10 MB", level="INFO")
    
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
    
    def fetch_article_content(self, url: str) -> Optional[Dict]:
        """获取微信公众号文章内容"""
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
            
            return self._parse_article_content(response.text, url)
            
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return self._fetch_with_selenium(url)
    
    def _fetch_with_selenium(self, url: str) -> Optional[Dict]:
        """使用Selenium获取文章内容"""
        try:
            self._init_selenium_driver()
            self.driver.get(url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rich_media_content"))
            )
            
            html_content = self.driver.page_source
            return self._parse_article_content(html_content, url)
            
        except Exception as e:
            logger.error(f"Selenium获取内容失败: {e}")
            return None
    
    def _parse_article_content(self, html_content: str, url: str) -> Dict:
        """解析文章内容"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 提取基本信息
        title = self._extract_title(soup)
        author = self._extract_author(soup)
        publish_time = self._extract_publish_time(soup)
        content = self._extract_content(soup)
        account_info = self._extract_account_info(soup)
        
        return {
            'url': url,
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'content': content,
            'account_info': account_info,
            'raw_html': html_content
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取文章标题"""
        title_selectors = [
            '#activity-name',
            '.rich_media_title',
            'h1',
            '.title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return "未找到标题"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者信息"""
        author_selectors = [
            '#js_name',
            '.rich_media_meta_text',
            '.author',
            '[data-author]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return "未找到作者"
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> str:
        """提取发布时间"""
        time_selectors = [
            '#publish_time',
            '.rich_media_meta_text',
            '[data-time]'
        ]
        
        for selector in time_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return "未找到发布时间"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取文章内容"""
        content_selectors = [
            '#js_content',
            '.rich_media_content',
            '.content'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return "未找到内容"
    
    def _extract_account_info(self, soup: BeautifulSoup) -> Dict:
        """提取公众号信息"""
        account_name = ""
        account_id = ""
        
        # 提取公众号名称
        name_element = soup.select_one('#js_name')
        if name_element:
            account_name = name_element.get_text().strip()
        
        # 提取公众号ID（从URL或页面中）
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # 查找包含公众号信息的脚本
                if 'biz' in script.string:
                    biz_match = re.search(r'biz=([^&"]+)', script.string)
                    if biz_match:
                        account_id = biz_match.group(1)
                        break
        
        return {
            'name': account_name,
            'id': account_id
        }
    
    def extract_copyright_info(self, article_data: Dict) -> Dict:
        """提取版权相关信息"""
        content = article_data.get('content', '')
        title = article_data.get('title', '')
        
        copyright_info = {
            'copyright_statements': [],
            'author_mentions': [],
            'source_mentions': [],
            'license_info': [],
            'contact_info': []
        }
        
        # 版权声明关键词
        copyright_patterns = [
            r'版权所有[：:](.*?)(?:\n|$)',
            r'©\s*(.*?)(?:\n|$)',
            r'Copyright\s*©?\s*(.*?)(?:\n|$)',
            r'著作权归(.*?)所有',
            r'本文版权归(.*?)所有',
            r'转载请注明(.*?)(?:\n|$)',
            r'原创作者[：:](.*?)(?:\n|$)',
            r'作者[：:](.*?)(?:\n|$)'
        ]
        
        for pattern in copyright_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                copyright_info['copyright_statements'].extend(matches)
        
        # 提取作者提及
        author_patterns = [
            r'作者[：:]\s*([^\n]+)',
            r'文[：:]\s*([^\n]+)',
            r'撰稿[：:]\s*([^\n]+)',
            r'编辑[：:]\s*([^\n]+)'
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, content)
            if matches:
                copyright_info['author_mentions'].extend(matches)
        
        # 提取来源信息
        source_patterns = [
            r'来源[：:]\s*([^\n]+)',
            r'出处[：:]\s*([^\n]+)',
            r'转载自[：:]\s*([^\n]+)',
            r'原文链接[：:]\s*([^\n]+)'
        ]
        
        for pattern in source_patterns:
            matches = re.findall(pattern, content)
            if matches:
                copyright_info['source_mentions'].extend(matches)
        
        # 提取联系信息
        contact_patterns = [
            r'微信[：:]\s*([^\n]+)',
            r'邮箱[：:]\s*([^\n]+)',
            r'联系[：:]\s*([^\n]+)',
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]
        
        for pattern in contact_patterns:
            matches = re.findall(pattern, content)
            if matches:
                copyright_info['contact_info'].extend(matches)
        
        return copyright_info
    
    def identify_author(self, article_data: Dict, copyright_info: Dict) -> Dict:
        """识别文章作者"""
        potential_authors = []
        
        # 从文章数据中获取作者
        if article_data.get('author'):
            potential_authors.append({
                'name': article_data['author'],
                'source': 'article_metadata',
                'confidence': 0.9
            })
        
        # 从版权信息中获取作者
        for author in copyright_info.get('author_mentions', []):
            potential_authors.append({
                'name': author.strip(),
                'source': 'copyright_statement',
                'confidence': 0.8
            })
        
        # 从版权声明中获取作者
        for statement in copyright_info.get('copyright_statements', []):
            potential_authors.append({
                'name': statement.strip(),
                'source': 'copyright_owner',
                'confidence': 0.7
            })
        
        # 去重和排序
        unique_authors = []
        seen_names = set()
        
        for author in sorted(potential_authors, key=lambda x: x['confidence'], reverse=True):
            name = author['name'].lower()
            if name not in seen_names and len(name.strip()) > 0:
                seen_names.add(name)
                unique_authors.append(author)
        
        return {
            'primary_author': unique_authors[0] if unique_authors else None,
            'all_potential_authors': unique_authors,
            'account_info': article_data.get('account_info', {})
        }
    
    def analyze_article(self, url: str) -> Dict:
        """分析文章的完整流程"""
        logger.info(f"开始分析文章: {url}")
        
        # 获取文章内容
        article_data = self.fetch_article_content(url)
        if not article_data:
            return {'error': '无法获取文章内容'}
        
        # 提取版权信息
        copyright_info = self.extract_copyright_info(article_data)
        
        # 识别作者
        author_info = self.identify_author(article_data, copyright_info)
        
        result = {
            'url': url,
            'title': article_data.get('title'),
            'publish_time': article_data.get('publish_time'),
            'account_info': article_data.get('account_info'),
            'copyright_info': copyright_info,
            'author_analysis': author_info,
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"分析完成: {article_data.get('title')}")
        return result
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()

def main():
    """主函数 - 命令行接口"""
    import sys
    
    if len(sys.argv) != 2:
        print("使用方法: python wechat_copyright_analyzer.py <微信文章链接>")
        sys.exit(1)
    
    url = sys.argv[1]
    analyzer = WeChatCopyrightAnalyzer()
    
    try:
        result = analyzer.analyze_article(url)
        
        if 'error' in result:
            print(f"错误: {result['error']}")
            sys.exit(1)
        
        # 输出结果
        print("\n=== 文章分析结果 ===")
        print(f"标题: {result['title']}")
        print(f"发布时间: {result['publish_time']}")
        print(f"公众号: {result['account_info']['name']}")
        
        print("\n=== 作者信息 ===")
        primary_author = result['author_analysis']['primary_author']
        if primary_author:
            print(f"主要作者: {primary_author['name']} (置信度: {primary_author['confidence']})")
            print(f"信息来源: {primary_author['source']}")
        else:
            print("未找到明确的作者信息")
        
        print("\n=== 版权信息 ===")
        copyright_info = result['copyright_info']
        if copyright_info['copyright_statements']:
            print("版权声明:")
            for statement in copyright_info['copyright_statements']:
                print(f"  - {statement}")
        
        if copyright_info['source_mentions']:
            print("来源信息:")
            for source in copyright_info['source_mentions']:
                print(f"  - {source}")
        
        if copyright_info['contact_info']:
            print("联系信息:")
            for contact in copyright_info['contact_info']:
                print(f"  - {contact}")
        
        print(f"\n分析时间: {result['analysis_time']}")
        
    except Exception as e:
        logger.error(f"分析过程中出现错误: {e}")
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()