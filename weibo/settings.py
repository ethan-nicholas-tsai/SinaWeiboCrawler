# -*- coding: utf-8 -*-
# Scrapy settings for weibo project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'weibo'
SPIDER_MODULES = ['weibo.spiders']
NEWSPIDER_MODULE = 'weibo.spiders'
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
LOG_LEVEL = "INFO"  # "INFO"
LOG_FILE = "weibo.log"
LOG_ENABLED = False

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 32  # search_com带cookie: 12, 不带cookie: 32
# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# 访问完一个页面再访问下一个时需要等待的时间，默认为10秒
# DOWNLOAD_DELAY = 10
DOWNLOAD_DELAY = 0  # 0.5  关键能瓶颈之一！！但是却是稳定性的保证
DOWNLOAD_TIMEOUT = 3  # 5s仍会出现TimeOut
RETRY_TIMES = 1  # 默认是3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 4  # 16
CONCURRENT_REQUESTS_PER_IP = 4  # 16
import random

# Configure request header
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    # 'cookie': 'your cookie'
 }
# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'weibo (+http://www.yourdomain.com)'
USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
    "Dalvik/1.6.0 (Linux; U; Android 4.2.1; 2013022 MIUI/JHACNBL30.0)",
    "Mozilla/5.0 (Linux; U; Android 4.4.2; zh-cn; HUAWEI MT7-TL00 Build/HuaweiMT7-TL00) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
    "AndroidDownloadManager",
    "Apache-HttpClient/UNAVAILABLE (java 1.4)",
    "Dalvik/1.6.0 (Linux; U; Android 4.3; SM-N7508V Build/JLS36C)",
    "Android50-AndroidPhone-8000-76-0-Statistics-wifi",
    "Dalvik/1.6.0 (Linux; U; Android 4.4.4; MI 3 MIUI/V7.2.1.0.KXCCNDA)",
    "Dalvik/1.6.0 (Linux; U; Android 4.4.2; Lenovo A3800-d Build/LenovoA3800-d)",
    "Lite 1.0 ( http://litesuits.com )",
    "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0",
    "Mozilla/5.0 (Linux; U; Android 4.1.1; zh-cn; HTC T528t Build/JRO03H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30; 360browser(securitypay,securityinstalled); 360(android,uppayplugin); 360 Aphone Browser (2.0.4)",
]

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # 禁用Scrapy自带的代理中间件与UA中间件，启用用户自定义的中间件
    'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
    'scrapy.contrib.downloadermiddleware.httpproxy.HttpProxyMiddleware': None,
    'scrapy.contrib.downloadermiddleware.retry.RetryMiddleware': None,
    'weibo.middlewares.UAMiddleware': 543,
    'weibo.middlewares.ProxyMiddleware': 544,
    # 'weibo.middlewares.CookieMiddleware': 545,
    'weibo.middlewares.MyRetryMiddleware': 546,
}
# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'weibo.pipelines.DuplicatesPipeline': 300,
    # 'weibo.pipelines.CsvPipeline': 301,
    # 'weibo.pipelines.MysqlPipeline': 302,
    'weibo.pipelines.MongoPipeline': 303,
    # 'weibo.pipelines.MyImagesPipeline': 304,
    # 'weibo.pipelines.MyVideoPipeline': 305
}
# @@@@@@@@@@@@@@@@@@@@@@@ 爬虫数据库配置 @@@@@@@@@@@@@@@@@@@@@@@@@@#
# 配置MongoDB数据库（全局）
MONGO_URI = 'YOUR_IP:YOUR_PORT'
MONGO_DATABASE = 'YOUR_DBNAME'
MONGO_USER = 'YOUR_USERNAME'
MONGO_PASSWORD = 'YOUR_PASSWORD'
# 配置MongoDB数据库（spiders）
MONGO_CNAME = {
    # 根据数据库中哪个集合来生成爬取任务
    'M_TASK': {
        'USER': 'm_user_state',
        'TWEET': 'm_task_state',
        'SUPERTOPIC': 'm_topic_state',
        'LONGTWEET': 'm_longtext_state'
    }
}
# @@@@@@@@@@@@@@@@@@@@@@@ COM站爬虫配置 @@@@@@@@@@@@@@@@@@@@@@@@@@#
# 要搜索的关键词列表，可写多个, 值可以是由关键词或话题组成的列表，也可以是包含关键词的txt文件路径，
# 如'keyword_list.txt'，txt文件中每个关键词占一行
# KEYWORD_LIST = ['抑郁 想死']  # 或者 KEYWORD_LIST = 'keyword_list.txt' #
# KEYWORD_LIST = ['抑郁 一无是处', '度洛西汀', '抑郁 生无可恋', '文拉法辛', '抑郁 舍曲林', '抑郁 没意思', '抑郁 难熬', '抑郁 自残', '抑郁 吃药', '抑郁 想哭', '抑郁 想死']
KEYWORD_LIST = ['#日常#']
# 要搜索的微博类型，0代表搜索全部微博，1代表搜索全部原创微博，2代表热门微博，3代表关注人微博，4代表认证用户微博，5代表媒体微博，6代表观点微博
WEIBO_TYPE = 1
# 筛选结果微博中必需包含的内容，0代表不筛选，获取全部微博，1代表搜索包含图片的微博，2代表包含视频的微博，3代表包含音乐的微博，4代表包含短链接的微博
CONTAIN_TYPE = 0
# 筛选微博的发布地区，精确到省或直辖市，值不应包含“省”或“市”等字，如想筛选北京市的微博请用“北京”而不是“北京市”，想要筛选安徽省的微博请用“安徽”而不是“安徽省”，可以写多个地区，
# 具体支持的地名见region.py文件，注意只支持省或直辖市的名字，省下面的市名及直辖市下面的区县名不支持，不筛选请用”全部“
REGION = ['全部']
# 搜索的起始日期，为yyyy-mm-dd形式，搜索结果包含该日期
# START_DATE = '2018-01-01'
START_DATE = '2014-01-01'
# 搜索的终止日期，为yyyy-mm-dd形式，搜索结果包含该日期
END_DATE = '2020-12-31'
# END_DATE = '2017-12-31'
# 搜索的时间段，0-24，搜索结果包含该时间，注释掉下面两条就是全天模式
# START_TIME = '0'
# END_TIME = '6'
# 进一步细分搜索的阈值，若结果页数大于等于该值，则认为结果没有完全展示，细分搜索条件重新搜索以获取更多微博。数值越大速度越快，也越有可能漏掉微博；数值越小速度越慢，获取的微博就越多。
# 建议数值大小设置在40到50之间。
FURTHER_THRESHOLD = 46
# 图片文件存储路径
IMAGES_STORE = './'
# 视频文件存储路径
FILES_STORE = './'
# 其他配置
USER_TYPE = 0  # 指定爬取的用户类型，对于二分类模型来说，1表示正例（抑郁），0表示负例
META_ONLY = True  # 是否只抓取元数据
# @@@@@@@@@@@@@@@@@@@@@@@ M站爬虫配置 @@@@@@@@@@@@@@@@@@@@@@@@@@#
# FILTER_RETWEET = False
MIN_WEIBO_CNT = 50
MAX_WEIBO_CNT = 500
# m_tweet配置
TASK_NUM_PER_ROUND = 1000  # 批量喂入任务，其实不用。。
# m_supertopic配置
TOPIC_ID = 'c86edb545da5818f5aad83caea7d75c1'  # 直接从container_id拷贝，前缀100808
TOPIC_NAME = '搞笑'
ORIENT_TYPE = 0
