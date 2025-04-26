# 中央纪委国家监委公开通报爬虫

这是一个基于Selenium的爬虫工具，用于爬取中央纪委国家监委网站的公开通报信息，包括列表页和详情页内容。

## 功能特点

- **多页爬取**：自动爬取多个页面的内容，默认爬取10页
- **详情页抓取**：访问每篇文章的详情页，获取完整内容
- **智能解析**：使用多种选择器策略，增强内容提取的成功率
- **数据完整**：提取标题、链接、摘要、正文、发布来源、发布时间等信息
- **健壮性设计**：完善的错误处理和异常捕获机制
- **友好交互**：详细的日志输出，实时展示爬取进度
- **灵活配置**：可自定义爬取页数和其他参数
- **反爬对策**：随机延时、自定义请求头，避免被网站封禁

## 环境要求

- Python 3.6+
- Chrome或Firefox浏览器（推荐使用Chrome）
- 相应的WebDriver（爬虫会尝试自动寻找）

## 依赖库

```
selenium==4.15.2
pandas==2.1.0
webdriver-manager==4.0.1
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 安装所需依赖库
2. 确保已安装Chrome或Firefox浏览器
3. 运行爬虫脚本：

```bash
python selenium_spider.py
```

4. 爬虫会自动执行以下操作：
   - 打开浏览器并访问目标网站
   - 爬取多个页面的内容（默认10页）
   - 访问每篇文章的详情页获取完整内容
   - 将爬取的数据保存为CSV和JSON格式
   - 将详情页HTML保存在article_details文件夹中

## 代码结构

- `selenium_spider.py`：主爬虫程序
- `requirements.txt`：依赖库列表
- `article_details/`：保存文章详情页HTML的文件夹
- `selenium_page_source.html`：保存第一页源码用于调试
- `ccdi_selenium_reports.csv`：CSV格式的爬取结果
- `ccdi_selenium_reports.json`：JSON格式的爬取结果

## 主要功能模块

- `CCDISeleniumSpider`类：爬虫的主类，包含所有爬取功能
- `setup_driver()`：设置Selenium浏览器驱动
- `crawl_multiple_pages()`：爬取多个页面的内容
- `crawl_page()`：爬取单个页面的内容
- `crawl_article_detail()`：爬取文章详情页
- `find_next_page_link()`：寻找下一页链接
- `get_total_pages()`：获取网站总页数
- `save_to_csv()`和`save_to_json()`：保存爬取结果

## 参数配置

关键参数可在`main()`函数中调整：

```python
# 设置要爬取的最大页数
max_pages = 10  # 可以根据需要调整
```

其他配置项：
- `with_details=True`：是否爬取详情页，设为False可以只爬取列表页
- `build_url(page_num)`：构建页面URL的方法，可根据网站变化调整

## 爬取的数据字段

爬虫会提取以下信息：

- `标题`：文章标题
- `链接`：文章URL
- `日期`：搜索结果页显示的日期
- `摘要`：文章摘要
- `正文`：文章详细内容
- `发布来源`：文章发布机构/来源
- `发布时间`：详细的文章发布时间
- `爬取页码`：数据来源的页码

## 优化与调整

1. **提高爬取速度**：
   - 在`crawl_multiple_pages()`中调整延时参数
   - 考虑启用浏览器的无头模式（headless mode）

2. **调整浏览器选项**：
   - 在`setup_driver()`方法中取消注释`options.add_argument('--headless')`

3. **增加爬取页数**：
   - 修改`main()`函数中的`max_pages`参数

## 注意事项

- 请合理设置爬取频率，避免对目标网站造成过大压力
- 爬取的内容仅供学习和研究使用，请遵守相关法律法规
- 如遇到网站结构变化，可能需要更新选择器策略
- 爬虫会保存详情页HTML，可能占用较大磁盘空间，请注意清理

## 更新日志

- 2023-04-26：添加多页爬取功能，支持爬取10页内容
- 2023-04-25：添加详情页爬取功能，提取文章正文和发布信息
- 2023-04-24：初始版本，实现基本的列表页爬取功能 