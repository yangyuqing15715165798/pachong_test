import time
import pandas as pd
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
import re
import random
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

class CCDIPlaywrightSpider:
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
        self.detail_folder = "article_details_playwright"  # 用于保存详情页HTML的文件夹
        self.pages_crawled = 0
        
        # 创建保存详情页的文件夹
        if not os.path.exists(self.detail_folder):
            os.makedirs(self.detail_folder)

    def build_url(self, page_num):
        """根据页码构建URL"""
        self.params['page'] = str(page_num)
        query_string = urlencode(self.params)
        return f"{self.base_url}?{query_string}"

    def setup_browser(self):
        """设置Playwright浏览器"""
        self.playwright = sync_playwright().start()
        
        try:
            # 尝试启动Chromium浏览器
            self.browser = self.playwright.chromium.launch(
                headless=False,  # 设置为True可启用无头模式
                slow_mo=50,  # 操作之间的延时，便于调试
            )
            print("成功启动Chromium浏览器")
            
            # 创建上下文，设置视口大小和用户代理
            self.context = self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            
            # 创建新页面
            self.page = self.context.new_page()
            
            # 设置超时时间(毫秒)
            self.page.set_default_timeout(30000)
            
        except Exception as e:
            print(f"启动浏览器失败: {e}")
            # 确保清理资源
            if hasattr(self, 'playwright'):
                self.playwright.stop()
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
            # 尝试查找页码信息
            pagination_info = self.page.query_selector('.page')
            if pagination_info:
                pagination_text = pagination_info.inner_text().strip()
                
                # 尝试提取总页数（格式可能是 "1/17"）
                if '/' in pagination_text:
                    parts = pagination_text.split('/')
                    for part in parts:
                        digits_only = ''.join(c for c in part if c.isdigit())
                        if digits_only.isdigit() and int(digits_only) > 1:
                            print(f"找到总页数: {digits_only}")
                            return int(digits_only)
            
            # 尝试从页码链接中找出最大页码
            page_links = self.page.query_selector_all('.page a')
            max_page = 0
            for link in page_links:
                link_text = link.inner_text().strip()
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
            self.page.goto(url, wait_until="networkidle")
            
            # 如果是第一页，保存页面源码以便调试
            page_num = self.get_current_page_number(url)
            if page_num == 1:
                with open('playwright_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(self.page.content())
                print("已保存第1页源码到playwright_page_source.html")
            
            # 等待列表项加载完成
            try:
                self.page.wait_for_selector('ul.s_0603_list', timeout=10000)
            except PlaywrightTimeoutError:
                print("未找到标准列表选择器，尝试其他方式...")
            
            # 查找所有列表项
            list_items = self.page.query_selector_all('ul.s_0603_list li')
            print(f"找到{len(list_items)}个列表项")
            
            if not list_items:
                # 如果没有找到列表项，尝试查找页面结构
                print("未找到列表项，正在分析页面结构...")
                all_uls = self.page.query_selector_all('ul')
                print(f"页面上共有 {len(all_uls)} 个ul元素")
                for i, ul in enumerate(all_uls[:5]):  # 只显示前5个，避免输出过多
                    class_attr = ul.get_attribute('class') or '无class'
                    print(f"第{i+1}个ul的class: {class_attr}")
                    
                # 尝试其他可能的选择器
                alternative_items = self.page.query_selector_all('.s_0603_list li, .center_box0 li, .other_center_22 li')
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
                        title_element = item.query_selector(selector)
                        if title_element:
                            break
                    
                    if not title_element:
                        print(f"无法找到标题元素，跳过: {item.inner_html()[:100]}...")
                        continue
                    
                    title = title_element.inner_text()
                    link = title_element.get_attribute('href')
                    
                    # 处理相对URL
                    if link and not link.startswith(('http://', 'https://')):
                        base_url_parts = urlparse(self.base_url)
                        base_url = f"{base_url_parts.scheme}://{base_url_parts.netloc}"
                        link = urljoin(base_url, link)
                    
                    # 提取日期
                    date = "无日期"
                    date_element = item.query_selector('span.time')
                    if date_element:
                        date = date_element.inner_text().strip()
                    else:
                        # 尝试其他日期选择器
                        date_element = item.query_selector('.time, .date')
                        if date_element:
                            date = date_element.inner_text().strip()
                    
                    # 提取摘要
                    summary = "无摘要"
                    summary_element = item.query_selector('em.emabstr i.abstract')
                    if summary_element:
                        summary = summary_element.inner_text().strip()
                        if not summary:
                            summary = "无摘要"
                    else:
                        # 尝试其他摘要选择器
                        summary_element = item.query_selector('.abstract, .summary, .description')
                        if summary_element:
                            summary = summary_element.inner_text().strip()
                    
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
                
        except PlaywrightTimeoutError:
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
            next_page = self.page.query_selector('.next-page')
            if next_page:
                return next_page.get_attribute('href')
            
            # 如果没有专门的下一页按钮，尝试从页码中找出当前页和下一页
            current_page = self.get_current_page_number(self.page.url)
            next_page_num = current_page + 1
            
            # 找到所有页码链接
            page_links = self.page.query_selector_all('.page a')
            for link in page_links:
                link_text = link.inner_text().strip()
                # 如果找到下一页的链接
                if link_text.isdigit() and int(link_text) == next_page_num:
                    return link.get_attribute('href')
            
            # 如果上述方法都失败，手动构建下一页URL
            return self.build_url(next_page_num)
            
        except Exception as e:
            print(f"查找下一页链接时出错: {e}")
            # 出错时尝试手动构建下一页URL
            current_page = self.get_current_page_number(self.page.url)
            return self.build_url(current_page + 1)

    def crawl_article_detail(self, url):
        """爬取文章详情页内容"""
        try:
            print(f"正在访问文章详情页: {url}")
            page = self.context.new_page()
            page.goto(url, wait_until="networkidle")
            
            # 处理可能出现的验证码
            if not self.handle_slider_captcha(page):
                print("验证码处理失败，可能影响详情页数据获取")
            
            # 等待页面加载完成
            page.wait_for_load_state('domcontentloaded')
            
            # 提取页面ID，用于保存HTML
            page_id = re.search(r'[^/]+\.html$', url)
            page_filename = page_id.group() if page_id else f"article_{int(time.time())}.html"
            
            # 保存详情页HTML以供调试
            detail_page_path = os.path.join(self.detail_folder, page_filename)
            with open(detail_page_path, 'w', encoding='utf-8') as f:
                f.write(page.content())
            
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
                content_element = page.query_selector(selector)
                if content_element:
                    # 清理正文中的多余空白
                    content = content_element.inner_text().strip()
                    content = re.sub(r'\s+', ' ', content)
                    result['正文'] = content
                    break
            
            # 2. 尝试提取发布来源
            source_selectors = [
                '.source', 
                '.article-source',
                '.info-source',
                '.ly',  # 中央纪委网站常用的来源标识
                '.source-time'
            ]
            
            for selector in source_selectors:
                source_element = page.query_selector(selector)
                if source_element:
                    source_text = source_element.inner_text().strip()
                    # 尝试从文本中提取来源信息
                    source_match = re.search(r'来源[:：]?\s*([^\s]+)', source_text)
                    if source_match:
                        result['发布来源'] = source_match.group(1)
                    else:
                        result['发布来源'] = source_text
                    break
            
            # 3. 尝试提取发布时间
            time_selectors = [
                '.time',
                '.article-time',
                '.info-time',
                '.date',
                '.sj'  # 中央纪委网站常用的时间标识
            ]
            
            for selector in time_selectors:
                time_element = page.query_selector(selector)
                if time_element:
                    time_text = time_element.inner_text().strip()
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
            
            # 关闭详情页面
            page.close()
            
            return result
            
        except Exception as e:
            print(f"爬取文章详情时出错: {e}")
            import traceback
            print(traceback.format_exc())
            
            # 确保页面被关闭，即使出错
            if 'page' in locals() and page:
                try:
                    page.close()
                except:
                    pass
                
            return None
    
    def save_to_csv(self, filename='ccdi_playwright_reports.csv'):
        """将结果保存为CSV文件"""
        if not self.results:
            print("没有数据可保存")
            return
        
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已保存至 {filename}，共{len(self.results)}条记录")
    
    def save_to_json(self, filename='ccdi_playwright_reports.json'):
        """将结果保存为JSON文件"""
        if not self.results:
            print("没有数据可保存")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存至 {filename}，共{len(self.results)}条记录")
    
    def close(self):
        """关闭浏览器和Playwright实例"""
        if hasattr(self, 'browser'):
            self.browser.close()
            print("浏览器已关闭")
        
        if hasattr(self, 'playwright'):
            self.playwright.stop()
            print("Playwright实例已停止")

def main():
    # 设置要爬取的最大页数
    max_pages = 3    # 可以根据需要调整
    
    spider = CCDIPlaywrightSpider()
    
    try:
        # 设置浏览器
        spider.setup_browser()
        
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