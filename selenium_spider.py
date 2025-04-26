import time
import pandas as pd
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import os
import re
import random
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

class CCDISeleniumSpider:
    def __init__(self):
        # 设置目标URL
        self.base_url = "https://www.ccdi.gov.cn/was5/web/search"
        self.params = {
            'page': '1',
            'channelid': '298814',
            'searchword': '中央纪委国家监委公开通报',
            'keyword': '中央纪委国家监委公开通报',
            'orderby': '-DocRelTime',
            'was_custom_expr': '(中央纪委国家监委公开通报)',
            'perpage': '10',
            'outlinepage': '10',
            'andsen': '',
            'total': '',
            'orsen': '中央纪委国家监委公开通报',
            'exclude': '',
            'searchscope': '',
            'timescope': '',
            'timescopecolumn': 'DocRelTime',
        }
        self.url = self.build_url(1)
        self.results = []
        self.detail_folder = "article_details"  # 用于保存详情页HTML的文件夹
        self.pages_crawled = 0
        
        # 创建保存详情页的文件夹
        if not os.path.exists(self.detail_folder):
            os.makedirs(self.detail_folder)

    def build_url(self, page_num):
        """根据页码构建URL"""
        self.params['page'] = str(page_num)
        query_string = urlencode(self.params)
        return f"{self.base_url}?{query_string}"

    def setup_driver(self):
        """设置Selenium浏览器驱动"""
        options = Options()
        
        # 添加一些选项以提高爬虫效率（可选）
        # options.add_argument('--headless')  # 无头模式，不显示浏览器窗口
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')  # 绕过部分反爬检测
        
        # 设置User-Agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        
        try:
            # 尝试直接创建驱动（如果webdriver在PATH中）
            self.driver = webdriver.Chrome(options=options)
            print("成功创建Chrome驱动")
        except Exception as e:
            print(f"创建Chrome驱动失败: {e}")
            print("尝试使用Firefox驱动...")
            
            try:
                # 尝试使用Firefox作为备选
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                # firefox_options.add_argument('--headless')
                self.driver = webdriver.Firefox(options=firefox_options)
                print("成功创建Firefox驱动")
            except Exception as e2:
                print(f"创建Firefox驱动也失败: {e2}")
                print("请确保已安装Chrome或Firefox浏览器，并设置了相应的webdriver")
                raise

    def crawl_multiple_pages(self, max_pages=5, with_details=True):
        """爬取多个页面的内容"""
        current_page = 1
        
        while current_page <= max_pages:
            print(f"\n====== 开始爬取第 {current_page} 页 ======\n")
            url = self.build_url(current_page)
            
            # 爬取当前页面
            page_items = self.crawl_page(url, with_details)
            
            if not page_items:
                print(f"第 {current_page} 页没有找到数据，爬取结束")
                break
                
            self.pages_crawled += 1
            current_page += 1
            
            # 随机延迟，避免请求过快
            if current_page <= max_pages:
                delay = random.uniform(2, 5)
                print(f"延时 {delay:.2f} 秒后继续爬取下一页...")
                time.sleep(delay)
        
        print(f"\n爬取完成！共爬取了 {self.pages_crawled} 页，获取 {len(self.results)} 条数据")

    def get_total_pages(self):
        """获取总页数"""
        try:
            # 找到页码信息
            pagination_info = self.driver.find_element(By.CSS_SELECTOR, '.page')
            pagination_text = pagination_info.text.strip()
            
            # 尝试提取总页数（格式可能是 "1/17"）
            if '/' in pagination_text:
                parts = pagination_text.split('/')
                for part in parts:
                    digits_only = ''.join(c for c in part if c.isdigit())
                    if digits_only.isdigit() and int(digits_only) > 1:
                        print(f"找到总页数: {digits_only}")
                        return int(digits_only)
            
            # 尝试从页码链接中找出最大页码
            page_links = self.driver.find_elements(By.CSS_SELECTOR, '.page a')
            max_page = 0
            for link in page_links:
                link_text = link.text.strip()
                # 如果链接文本是数字，可能是页码
                if link_text.isdigit():
                    page_num = int(link_text)
                    max_page = max(max_page, page_num)
            
            if max_page > 0:
                print(f"从链接找到最大页码: {max_page}")
                return max_page
            
            # 如果上述方法都失败，返回默认值
            return 5
            
        except Exception as e:
            print(f"获取总页数时出错: {e}")
            # 出错时返回保守值
            return 5

    def crawl_page(self, url, with_details=True):
        """爬取指定URL的页面内容"""
        try:
            print(f"正在访问页面: {url}")
            self.driver.get(url)
            
            # 等待页面加载完成（等待结果列表出现）
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.s_0603_list')))
            
            # 如果是第一页，保存页面源码以便调试
            page_num = self.get_current_page_number(url)
            if page_num == 1:
                with open('selenium_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("已保存第1页源码到selenium_page_source.html")
            
            # 查找所有列表项
            list_items = self.driver.find_elements(By.CSS_SELECTOR, 'ul.s_0603_list li')
            print(f"找到{len(list_items)}个列表项")
            
            if not list_items:
                # 如果没有找到列表项，尝试查找页面结构
                print("未找到列表项，正在分析页面结构...")
                all_uls = self.driver.find_elements(By.TAG_NAME, 'ul')
                print(f"页面上共有 {len(all_uls)} 个ul元素")
                for i, ul in enumerate(all_uls[:5]):  # 只显示前5个，避免输出过多
                    print(f"第{i+1}个ul的class: {ul.get_attribute('class')}")
                    
                # 尝试其他可能的选择器
                alternative_items = self.driver.find_elements(By.CSS_SELECTOR, '.s_0603_list li, .center_box0 li, .other_center_22 li')
                print(f"使用备选选择器找到{len(alternative_items)}个列表项")
                list_items = alternative_items if alternative_items else list_items
            
            # 处理每个列表项
            article_links = []  # 存储文章链接，用于后续爬取详情
            page_items = []  # 存储当前页的数据
            
            for item in list_items:
                try:
                    # 使用不同的选择器组合尝试提取标题和链接
                    title_element = None
                    selectors = [
                        'em.emtitle b.title a', 
                        'b.title a', 
                        'a', 
                        'em a', 
                        '.title a'
                    ]
                    
                    for selector in selectors:
                        try:
                            title_element = item.find_element(By.CSS_SELECTOR, selector)
                            if title_element:
                                break
                        except NoSuchElementException:
                            continue
                    
                    if not title_element:
                        print(f"无法找到标题元素，跳过: {item.get_attribute('outerHTML')[:100]}...")
                        continue
                    
                    title = title_element.text
                    link = title_element.get_attribute('href')
                    
                    # 提取日期
                    date = "无日期"
                    try:
                        date_element = item.find_element(By.CSS_SELECTOR, 'span.time')
                        date = date_element.text.strip()
                    except NoSuchElementException:
                        try:
                            # 尝试其他日期选择器
                            date_element = item.find_element(By.CSS_SELECTOR, '.time, .date, span:contains("20")')
                            date = date_element.text.strip()
                        except Exception:
                            pass
                    
                    # 提取摘要
                    summary = "无摘要"
                    try:
                        summary_element = item.find_element(By.CSS_SELECTOR, 'em.emabstr i.abstract')
                        summary = summary_element.text.strip()
                        if not summary:
                            summary = "无摘要"
                    except NoSuchElementException:
                        try:
                            # 尝试其他摘要选择器
                            summary_element = item.find_element(By.CSS_SELECTOR, '.abstract, .summary, .description')
                            summary = summary_element.text.strip()
                        except Exception:
                            pass
                    
                    # 添加到结果
                    article_data = {
                        '标题': title,
                        '链接': link,
                        '日期': date,
                        '摘要': summary,
                        '正文': "",
                        '发布来源': "",
                        '发布时间': "",
                        '爬取页码': page_num
                    }
                    
                    self.results.append(article_data)
                    page_items.append(article_data)
                    article_links.append((len(self.results) - 1, link))  # 保存索引和链接，用于更新结果
                    print(f"成功解析: {title}")
                
                except Exception as e:
                    print(f"解析列表项时出错: {e}")
            
            print(f"第{page_num}页共解析 {len(page_items)} 条数据")
            
            # 爬取详情页
            if with_details and article_links:
                print(f"\n正在爬取第{page_num}页的文章详情...")
                for idx, link in article_links:
                    try:
                        detail_data = self.crawl_article_detail(link)
                        if detail_data:
                            # 更新结果中的详情数据
                            self.results[idx].update(detail_data)
                            print(f"已获取详情: {self.results[idx]['标题']}")
                        else:
                            print(f"未能获取详情: {self.results[idx]['标题']}")
                        
                        # 每个详情页之间添加小延迟，避免请求过快
                        time.sleep(random.uniform(0.5, 1.5))
                    except Exception as e:
                        print(f"获取详情页时出错: {e}")
                
                print(f"第{page_num}页所有详情页爬取完成！")
            
            return page_items
                
        except TimeoutException:
            print("页面加载超时，请检查网络连接或网站是否可访问")
            return []
        except Exception as e:
            print(f"爬取页面时出错: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    def get_current_page_number(self, url):
        """从URL中提取当前页码"""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        if 'page' in query_params:
            return int(query_params['page'][0])
        return 1

    def find_next_page_link(self):
        """找到下一页的链接"""
        try:
            # 尝试找到"下一页"按钮
            next_page = self.driver.find_element(By.CSS_SELECTOR, '.next-page')
            if next_page:
                return next_page.get_attribute('href')
            
            # 如果没有专门的下一页按钮，尝试从页码中找出当前页和下一页
            current_page = self.get_current_page_number(self.driver.current_url)
            next_page_num = current_page + 1
            
            # 找到所有页码链接
            page_links = self.driver.find_elements(By.CSS_SELECTOR, '.page a')
            for link in page_links:
                link_text = link.text.strip()
                # 如果找到下一页的链接
                if link_text.isdigit() and int(link_text) == next_page_num:
                    return link.get_attribute('href')
            
            # 如果上述方法都失败，手动构建下一页URL
            return self.build_url(next_page_num)
            
        except Exception as e:
            print(f"查找下一页链接时出错: {e}")
            # 出错时尝试手动构建下一页URL
            current_page = self.get_current_page_number(self.driver.current_url)
            return self.build_url(current_page + 1)

    def crawl_article_detail(self, url):
        """爬取文章详情页内容"""
        try:
            print(f"正在访问文章详情页: {url}")
            self.driver.get(url)
            
            # 等待页面加载完成
            time.sleep(2)
            
            # 提取页面ID，用于保存HTML
            page_id = re.search(r'[^/]+\.html$', url)
            page_filename = page_id.group() if page_id else f"article_{int(time.time())}.html"
            
            # 保存详情页HTML以供调试
            detail_page_path = os.path.join(self.detail_folder, page_filename)
            with open(detail_page_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # 尝试不同的选择器提取内容
            result = {}
            
            # 1. 尝试提取正文
            content_selectors = [
                '.TRS_Editor',  # 常见的正文容器
                '.article-content', 
                '.content',
                '#content',
                '.detail-content',
                '.w1100'  # 中央纪委网站常用的内容容器
            ]
            
            for selector in content_selectors:
                try:
                    content_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if content_element:
                        # 清理正文中的多余空白
                        content = content_element.text.strip()
                        content = re.sub(r'\s+', ' ', content)
                        result['正文'] = content
                        break
                except NoSuchElementException:
                    continue
            
            # 2. 尝试提取发布来源
            source_selectors = [
                '.source', 
                '.article-source',
                '.info-source',
                '.ly',  # 中央纪委网站常用的来源标识
                '.source-time'
            ]
            
            for selector in source_selectors:
                try:
                    source_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if source_element:
                        source_text = source_element.text.strip()
                        # 尝试从文本中提取来源信息
                        source_match = re.search(r'来源[:：]?\s*([^\s]+)', source_text)
                        if source_match:
                            result['发布来源'] = source_match.group(1)
                        else:
                            result['发布来源'] = source_text
                        break
                except NoSuchElementException:
                    continue
            
            # 3. 尝试提取发布时间
            time_selectors = [
                '.time',
                '.article-time',
                '.info-time',
                '.date',
                '.sj'  # 中央纪委网站常用的时间标识
            ]
            
            for selector in time_selectors:
                try:
                    time_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if time_element:
                        time_text = time_element.text.strip()
                        # 尝试从文本中提取时间信息
                        time_match = re.search(r'(\d{4}[-年/]\d{1,2}[-月/]\d{1,2}日?\s*\d{1,2}:\d{1,2}(:\d{1,2})?)', time_text)
                        if time_match:
                            result['发布时间'] = time_match.group(1)
                        else:
                            time_match = re.search(r'(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})', time_text)
                            if time_match:
                                result['发布时间'] = time_match.group(1)
                            else:
                                result['发布时间'] = time_text
                        break
                except NoSuchElementException:
                    continue
            
            return result
            
        except Exception as e:
            print(f"爬取文章详情时出错: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def save_to_csv(self, filename='ccdi_selenium_reports.csv'):
        """将结果保存为CSV文件"""
        if not self.results:
            print("没有数据可保存")
            return
        
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已保存至 {filename}，共{len(self.results)}条记录")
    
    def save_to_json(self, filename='ccdi_selenium_reports.json'):
        """将结果保存为JSON文件"""
        if not self.results:
            print("没有数据可保存")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存至 {filename}，共{len(self.results)}条记录")
    
    def close(self):
        """关闭浏览器驱动"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("浏览器驱动已关闭")

def main():
    # 设置要爬取的最大页数
    max_pages = 10    # 可以根据需要调整
    
    spider = CCDISeleniumSpider()
    
    try:
        # 设置浏览器驱动
        spider.setup_driver()
        
        # 爬取多个页面
        spider.crawl_multiple_pages(max_pages=max_pages, with_details=True)
        
        # 保存数据
        spider.save_to_csv()
        spider.save_to_json()
        
        print("爬取完成！")
    
    finally:
        # 确保浏览器正常关闭
        spider.close()

if __name__ == "__main__":
    main() 