# CCDI Web Scraper

## 描述

这是一个使用 Python 编写的网络爬虫，用于从中央纪委国家监委网站 (`www.ccdi.gov.cn`) 抓取特定主题（"中央纪委国家监委公开通报"）的搜索结果。脚本能够爬取文章列表，并进一步访问每个文章的详情页以提取正文、来源和发布时间。

项目提供了两个版本的爬虫实现：
- **Selenium版本**：使用Selenium WebDriver驱动浏览器进行爬取
- **Playwright版本**：使用Microsoft Playwright驱动浏览器进行爬取

## 功能特性

*   **多页爬取:** 能够自动翻页并爬取指定数量的搜索结果页面。
*   **详情提取:** 访问列表中的文章链接，抓取文章详情页的内容（正文、来源、时间）。
*   **动态 URL 构建:** 根据页码动态生成目标 URL。
*   **健壮性:**
    *   尝试使用多种 CSS 选择器来定位元素，提高对页面结构变化的适应性。
    *   包含基本的错误处理（超时、元素未找到）。
    *   优先尝试 Chrome/Chromium 浏览器，Selenium版本还提供Firefox备选。
*   **数据存储:** 将抓取结果保存为 CSV 和 JSON 两种格式。
*   **HTML 存档:** 将每个文章详情页的 HTML 源码保存到本地文件夹，便于调试和离线分析。
*   **反爬规避:**
    *   设置了常见的浏览器 User-Agent。
    *   在页面和详情页请求之间加入了随机延时。

## 版本对比

### Selenium版本 (`selenium_spider.py`)
- 使用成熟的Selenium库，兼容性较好
- 支持Chrome和Firefox两种浏览器
- 使用WebDriverWait进行显式等待
- 详情页HTML保存在`article_details`文件夹
- 数据保存为`ccdi_selenium_reports.csv`和`ccdi_selenium_reports.json`

### Playwright版本 (`playwright_spider.py`)
- 使用现代化的Playwright库，性能更好
- 内置更智能的等待机制
- 对新型网页和前端框架支持更好
- 详情页HTML保存在`article_details_playwright`文件夹
- 为每个详情页打开独立的标签页，不影响主页面
- 数据保存为`ccdi_playwright_reports.csv`和`ccdi_playwright_reports.json`

## 技术栈

### 共同依赖
*   **Python 3.x**
*   **Pandas:** 用于数据处理和导出为 CSV 文件。
*   **JSON:** Python 内置库，用于导出为 JSON 文件。
*   **Urllib:** 用于 URL 解析和构建。
*   **Re (正则表达式):** 用于从文本中提取特定格式的信息。
*   **OS, Time, Random:** Python 内置库，用于文件操作、延时和随机数生成。

### Selenium版本特有
*   **Selenium:** 核心的浏览器自动化和网页抓取库。
*   **WebDrivers:** 需要安装 [ChromeDriver](https://chromedriver.chromium.org/downloads) 或 [GeckoDriver](https://github.com/mozilla/geckodriver/releases) (Firefox)。

### Playwright版本特有
*   **Playwright:** 微软开发的现代化浏览器自动化库。
*   **内置浏览器引擎:** 不需要单独安装WebDriver，Playwright会自动下载和管理浏览器。

## 安装与设置

1.  **克隆仓库或下载代码:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```
2.  **安装 Python 依赖:**
    建议在虚拟环境中安装。
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # 或者
    # venv\Scripts\activate  # Windows

    pip install -r requirements.txt
    ```
3.  **Selenium专属设置:**
    *   确保你安装了 Chrome 或 Firefox 浏览器。
    *   下载与你的浏览器版本对应的 WebDriver:
        *   [ChromeDriver](https://chromedriver.chromium.org/downloads)
        *   [GeckoDriver (for Firefox)](https://github.com/mozilla/geckodriver/releases)
    *   将下载的 WebDriver 可执行文件放置在系统的 PATH 环境变量所包含的目录下，或者直接放在项目根目录下。

4.  **Playwright专属设置:**
    *   安装Playwright后，运行以下命令自动下载必要的浏览器:
        ```bash
        python -m playwright install
        ```

## 如何运行

### 运行Selenium版爬虫:

```bash
python selenium_spider.py
```

### 运行Playwright版爬虫:

```bash
python playwright_spider.py
```

*   默认情况下，脚本会尝试爬取前 `3` 页的搜索结果（可以在各自 `main` 函数中的 `max_pages` 变量修改）。
*   脚本运行时会在控制台打印当前的爬取状态和进度信息。

## 输出

### Selenium版本输出:
*   `ccdi_selenium_reports.csv`: 包含所有爬取到的文章信息的 CSV 文件。
*   `ccdi_selenium_reports.json`: 包含所有爬取到的文章信息的 JSON 文件。
*   `article_details/` (目录): 包含所有成功访问的文章详情页的 HTML 源码文件。
*   `selenium_page_source.html`: (如果爬取了第一页) 第一页列表页面的 HTML 源码，用于调试。

### Playwright版本输出:
*   `ccdi_playwright_reports.csv`: 包含所有爬取到的文章信息的 CSV 文件。
*   `ccdi_playwright_reports.json`: 包含所有爬取到的文章信息的 JSON 文件。
*   `article_details_playwright/` (目录): 包含所有成功访问的文章详情页的 HTML 源码文件。
*   `playwright_page_source.html`: (如果爬取了第一页) 第一页列表页面的 HTML 源码，用于调试。

## 代码结构

### 两个版本的爬虫主类:
*   **`CCDISeleniumSpider` (Selenium版)与 `CCDIPlaywrightSpider` (Playwright版):** 封装了爬虫的主要逻辑。
    
    两个类结构基本一致，主要方法包括:
    *   `__init__`: 初始化 URL、参数、结果列表、文件夹路径等。
    *   `build_url`: 根据页码构建完整的请求 URL。
    *   `setup_driver`/`setup_browser`: 配置并初始化浏览器实例。
    *   `crawl_multiple_pages`: 控制爬取多个页面的主循环。
    *   `get_total_pages`: 尝试从页面获取总页数。
    *   `crawl_page`: 爬取单个列表页，提取文章基本信息，并调用详情页爬取。
    *   `get_current_page_number`: 从 URL 中提取当前页码。
    *   `find_next_page_link`: 尝试查找"下一页"的链接。
    *   `crawl_article_detail`: 爬取单个文章详情页，提取正文、来源、时间，并保存 HTML。
    *   `save_to_csv`: 将结果保存为 CSV。
    *   `save_to_json`: 将结果保存为 JSON。
    *   `close`: 关闭浏览器实例和清理资源。
*   **`main()` 函数:** 程序入口，创建爬虫实例，调用爬取和保存方法，并确保资源正确关闭。
*   **`if __name__ == "__main__":`:** 确保 `main()` 函数只在脚本直接运行时执行。

## 两个版本的主要区别

### Selenium与Playwright的API区别:
*   **元素定位:**
    - Selenium: `driver.find_element(By.CSS_SELECTOR, 'selector')`
    - Playwright: `page.query_selector('selector')`
*   **元素集合:**
    - Selenium: `driver.find_elements(By.CSS_SELECTOR, 'selector')`
    - Playwright: `page.query_selector_all('selector')`
*   **获取文本:**
    - Selenium: `element.text`
    - Playwright: `element.inner_text()`
*   **获取属性:**
    - Selenium: `element.get_attribute('href')`
    - Playwright: `element.get_attribute('href')`
*   **等待机制:**
    - Selenium: 需要显式使用`WebDriverWait`
    - Playwright: 内置等待机制，如`wait_for_selector`, `wait_for_load_state`等
*   **浏览器管理:**
    - Selenium: 需要WebDriver，更复杂的浏览器初始化流程
    - Playwright: 内置浏览器管理，提供更简洁的浏览器、上下文和页面层级结构

## 注意事项

*   **网站结构变化:** 网站的 HTML 结构可能会改变，导致 CSS 选择器失效。如果脚本无法正常抓取数据，需要检查网站源码并更新选择器。
*   **反爬虫机制:** 目标网站可能存在更复杂的反爬虫措施。如果遇到频繁的失败或验证码，可能需要更高级的技术（如代理 IP、更复杂的请求头模拟、验证码识别服务等）。
*   **浏览器兼容性:** 确保你的环境能够正常启动浏览器。Playwright版本需要确保你有足够的权限安装和启动浏览器。
*   **法律和道德:** 请遵守目标网站的 `robots.txt` 文件（如果存在）和服务条款。负责任地进行网络爬取，避免对网站服务器造成过大负担。

## 更新日志

- 2025-05-12：添加基于Playwright的爬虫实现
- 2025-04-26：添加多页爬取功能，支持爬取10页内容
- 2025-04-25：添加详情页爬取功能，提取文章正文和发布信息
- 2025-04-24：初始版本，实现基本的列表页爬取功能 