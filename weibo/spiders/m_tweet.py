#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/12/19 13:07
# @Author  : cendeavor
# @File    : cn_tweet.py
# @Software: PyCharm

"""
此程序依赖三张表
UserState:    不直接用于本程序，其他程序根据这张表生成本程序需要的TaskState表
    _id              用户id
    account_alive    用户账号是否存活
    state            是否爬完微博
    weibo_count      用户微博数
    crawled_time     最后一次爬取该用户的时间
TaskState:    本程序直接使用的任务表
    _id              用户id
    weibo_count      用户微博数
    state            记录用户每页是否爬到, 01序列字符串
    done             用户微博是否爬完(冗余)
RequestState: 用于本程序，并在程序结束后由其他程序进行清算统计生成TaskState中的state和done
    _id              用户id加页数（_id#page格式）
"""

import sys
import time
from collections import OrderedDict
from datetime import date, datetime, timedelta
import scrapy
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from requests.adapters import HTTPAdapter
import json
from lxml import etree
import logging
import weibo.utils.util as util
from weibo.items.m import UserStateItem, TweetItem, RequestStateItem
from database_connector import MongoDBC
from scrapy.utils.project import get_project_settings

settings = get_project_settings()


class TweetSpider(scrapy.Spider):
    name = 'tweet_m'
    allowed_domains = ['m.weibo.cn', 'weibo.com']  # crawling sites
    base_url = 'https://m.weibo.cn/'
    api = {
        # 此api如果带上cookie就能基本爬全。。
        'tweet_page': {
            '0': 'api/container/getIndex?containerid=107603',
            # +uid
            '1': '&page='
        },
        'longtext': 'statuses/extend?id=',  # +tid(numerical)
        # detail 比longtext的唯一优势在于，对于pic_num > 9的情况，还能获取所有的pic_url
        'tweet_detail': 'detail/'  # +tid(numerical), 其实不是api，只是通过这个链接访问特定的推文，也可把detail换成status
    }
    page_cnt = 0

    def __init__(self, *args, **kwargs):
        super(TweetSpider, self).__init__(*args, **kwargs)
        uri = settings.get('MONGO_URI')
        dbname = settings.get('MONGO_DATABASE')
        username = settings.get('MONGO_USER')
        password = settings.get('MONGO_PASSWORD')
        self.dbc = MongoDBC(uri, dbname, username, password)
        try:
            self.db = self.dbc.connect()
        except Exception as e:
            self.logger.log(msg=e, level=logging.ERROR)
            sys.exit(e)
        self.cname = settings.get('MONGO_CNAME')['M_TASK']['TWEET']
        self.logger.debug('[m_tweet]: get task from {}'.format(self.cname))

    def requests_get(self, url, timeout=3, max_retries=2):
        # 超时重试机制 + cookie + random ua + proxy pool
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=max_retries))
        s.mount('https://', HTTPAdapter(max_retries=max_retries))
        try:
            headers, proxies = util.get_headers_and_proxies()
            r = s.get(url, headers=headers, proxies=proxies,
                      timeout=timeout, verify=False)  # requests自动会对url进行编码
            return r
        except requests.exceptions.RequestException as e:
            self.logger.log(msg=e, level=logging.ERROR)
            return None

    def generate_tweet_page_url(self, uid, page=None):
        tweet_page_url = self.base_url + self.api['tweet_page']['0'] + str(uid)
        if page:
            tweet_page_url += self.api['tweet_page']['1'] + str(page)
        return tweet_page_url

    def generate_longtext_url(self, tid):
        return self.base_url + self.api['longtext'] + str(tid)

    def generate_tweet_detail_url(self, tid):
        return self.base_url + self.api['tweet_detail'] + str(tid)

    def start_requests(self):
        """ override the start of request

        Returns:

        """
        # TODO: 数据库/文件/配置多种方式生成任务
        # 利用上下文管理器防止python异常终端导致游标无法清除而占用 Mongodb 资源
        with self.db[self.cname].find({}, no_cursor_timeout=True) as cursor:
            for item in cursor:
                uid = item['_id']
                # if not item['state']:
                #     page_list = [i for i in range(int(math.ceil(item['weibo_count'] / 10.0)))]
                # else:  # item['state']为01组成的序列，从右往左为第1到最后一页是否爬取完成, 0表示没有爬取完成
                page_list = [i for i in range(1, len(item['state']) + 1) if item['state'][-i] == '0']
                for page in page_list:
                    yield scrapy.Request(url=self.generate_tweet_page_url(uid=uid, page=page),
                                         callback=self.parse_tweets,
                                         meta={'uid': uid, 'page': page})
                # TODO: 想一个简单点的更新方法(此处不能，scrapy的start_requests只允许yield Request对象)
                # 更新用户推文爬取时间
                # user_state_item = UserStateItem()
                # user_state_item['_id'] = item['_id']
                # user_state_item['account_alive'] = True
                # user_state_item['state'] = item['state']
                # user_state_item['weibo_count'] = item['weibo_count']
                # user_state_item['crawled_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                # yield user_state_item
        self.dbc.close()

    @staticmethod
    def get_pics(weibo_info):
        """获取微博原始图片url"""
        if weibo_info.get('pics'):
            pic_info = weibo_info['pics']
            pic_list = [pic['large']['url'] for pic in pic_info]
            pics = ','.join(pic_list)
        else:
            pics = ''
        return pics

    @staticmethod
    def get_live_photo(weibo_info):
        """获取live photo中的视频url"""
        live_photo_list = []
        live_photo = weibo_info.get('pic_video')
        if live_photo:
            prefix = 'https://video.weibo.com/media/play?livephoto=//us.sinaimg.cn/'
            for i in live_photo.split(','):
                if len(i.split(':')) == 2:
                    url = prefix + i.split(':')[1] + '.mov'
                    live_photo_list.append(url)
            return live_photo_list

    def get_video_url(self, weibo_info):
        """获取微博视频url"""
        video_url = ''
        video_url_list = []
        if weibo_info.get('page_info'):
            if weibo_info['page_info'].get('media_info') and weibo_info[
                'page_info'].get('type') == 'video':
                media_info = weibo_info['page_info']['media_info']
                video_url = media_info.get('mp4_720p_mp4')
                if not video_url:
                    video_url = media_info.get('mp4_hd_url')
                    if not video_url:
                        video_url = media_info.get('mp4_sd_url')
                        if not video_url:
                            video_url = media_info.get('stream_url_hd')
                            if not video_url:
                                video_url = media_info.get('stream_url')
        if video_url:
            video_url_list.append(video_url)
        live_photo_list = self.get_live_photo(weibo_info)
        if live_photo_list:
            video_url_list += live_photo_list
        return ';'.join(video_url_list)

    @staticmethod
    def get_location(selector):
        """获取微博发布位置"""
        location_icon = 'timeline_card_small_location_default.png'
        span_list = selector.xpath('//span')
        location = ''
        for i, span in enumerate(span_list):
            if span.xpath('img/@src'):
                if location_icon in span.xpath('img/@src')[0]:
                    location = span_list[i + 1].xpath('string(.)')
                    break
        return location

    @staticmethod
    def get_article_url(selector):
        """获取微博中头条文章的url"""
        article_url = ''
        text = selector.xpath('string(.)')
        if text.startswith(u'发布了头条文章'):
            url = selector.xpath('//a/@data-url')
            if url and url[0].startswith('http://t.cn'):
                article_url = url[0]
        return article_url

    @staticmethod
    def get_topics(selector):
        """获取参与的微博话题"""
        span_list = selector.xpath("//span[@class='surl-text']")
        topics = ''
        topic_list = []
        for span in span_list:
            text = span.xpath('string(.)')
            if len(text) > 2 and text[0] == '#' and text[-1] == '#':
                topic_list.append(text[1:-1])
        if topic_list:
            topics = ','.join(topic_list)
        return topics

    @staticmethod
    def get_at_users(selector):
        """获取@用户"""
        a_list = selector.xpath('//a')
        at_users = ''
        at_list = []
        for a in a_list:
            if '@' + a.xpath('@href')[0][3:] == a.xpath('string(.)'):
                at_list.append(a.xpath('string(.)')[1:])
        if at_list:
            at_users = ','.join(at_list)
        return at_users

    @staticmethod
    def string_to_int(string):
        """字符串转换为整数"""
        if isinstance(string, int):
            return string
        elif string.endswith(u'万+'):
            string = int(string[:-2] + '0000')
        elif string.endswith(u'万'):
            string = int(string[:-1] + '0000')
        return int(string)

    @staticmethod
    def standardize_date(created_at):
        """标准化微博发布时间"""
        if u'刚刚' in created_at:
            created_at = datetime.now().strftime('%Y-%m-%d')
        elif u'分钟' in created_at:
            minute = created_at[:created_at.find(u'分钟')]
            minute = timedelta(minutes=int(minute))
            created_at = (datetime.now() - minute).strftime('%Y-%m-%d')
        elif u'小时' in created_at:
            hour = created_at[:created_at.find(u'小时')]
            hour = timedelta(hours=int(hour))
            created_at = (datetime.now() - hour).strftime('%Y-%m-%d')
        elif u'昨天' in created_at:
            day = timedelta(days=1)
            created_at = (datetime.now() - day).strftime('%Y-%m-%d')
        else:
            created_at = created_at.replace('+0800 ', '')
            temp = datetime.strptime(created_at, '%c')
            created_at = datetime.strftime(temp, '%Y-%m-%d')
        return created_at

    @staticmethod
    def standardize_info(weibo):
        """标准化信息，去除乱码"""
        for k, v in weibo.items():
            if 'bool' not in str(type(v)) and 'int' not in str(
                    type(v)) and 'list' not in str(
                type(v)) and 'long' not in str(type(v)):
                weibo[k] = v.replace(u'\u200b', '').encode(
                    sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding)
        return weibo

    def parse_weibo(self, weibo_info):
        weibo = OrderedDict()
        if weibo_info['user']:
            weibo['user_id'] = weibo_info['user']['id']
            weibo['screen_name'] = weibo_info['user']['screen_name']
        else:
            weibo['user_id'] = ''
            weibo['screen_name'] = ''
        weibo['id'] = int(weibo_info['id'])
        weibo['bid'] = weibo_info['bid']
        text_body = weibo_info['text']
        selector = etree.HTML(text_body)
        weibo['text'] = text_body
        # weibo['text'] = etree.HTML(text_body).xpath('string(.)')
        weibo['article_url'] = self.get_article_url(selector)
        weibo['pics'] = self.get_pics(weibo_info)
        weibo['video_url'] = self.get_video_url(weibo_info)
        weibo['location'] = self.get_location(selector)
        weibo['created_at'] = weibo_info['created_at']
        weibo['source'] = weibo_info['source']
        weibo['attitudes_count'] = self.string_to_int(
            weibo_info.get('attitudes_count', 0))
        weibo['comments_count'] = self.string_to_int(
            weibo_info.get('comments_count', 0))
        weibo['reposts_count'] = self.string_to_int(
            weibo_info.get('reposts_count', 0))
        weibo['topics'] = self.get_topics(selector)
        weibo['at_users'] = self.get_at_users(selector)
        # 可能有用字段
        weibo['isLongText'] = weibo_info.get('isLongText', '')
        weibo['darwin_tags'] = weibo_info.get('darwin_tags', [])
        weibo['photoTag'] = weibo_info.get('photoTag', [])
        weibo['edit_count'] = weibo_info.get('edit_count', 0)
        weibo['edit_at'] = weibo_info.get('edit_at', '')
        return self.standardize_info(weibo)

    def get_long_weibo(self, tid):
        """获取长微博"""
        r = self.requests_get(self.generate_tweet_detail_url(tid=tid), timeout=5, max_retries=3)
        if not r:
            return None
        html = r.text
        html = html[html.find('"status":'):]
        html = html[:html.rfind('"hotScheme"')]
        html = html[:html.rfind(',')]
        html = '{' + html + '}'
        try:
            js = json.loads(html, strict=False)
            weibo_info = js.get('status')  # 长微博的所有信息，只是将text换成了long_text
            if weibo_info:
                weibo = self.parse_weibo(weibo_info)
                return weibo
        except Exception as e:
            self.logger.log(msg=e, level=logging.WARNING)
            return None

    def get_one_weibo(self, info):
        """获取一条微博的全部信息"""
        try:
            weibo_info = info['mblog']
            weibo_id = weibo_info['id']
            retweeted_status = weibo_info.get('retweeted_status')
            is_long = True if weibo_info.get(
                'pic_num') > 9 else weibo_info.get('isLongText')  # pic_num > 9在tweet_page api中获取不全！
            if retweeted_status and retweeted_status.get('id'):  # 转发
                retweet_id = retweeted_status.get('id')
                is_long_retweet = retweeted_status.get('isLongText')
                if is_long:
                    weibo = self.get_long_weibo(weibo_id)
                    if not weibo:
                        weibo = self.parse_weibo(weibo_info)
                        weibo['getLongText'] = False
                    else:
                        weibo['getLongText'] = True
                else:
                    weibo = self.parse_weibo(weibo_info)
                if is_long_retweet:
                    retweet = self.get_long_weibo(retweet_id)
                    if not retweet:
                        retweet = self.parse_weibo(retweeted_status)
                        retweet['getLongText'] = False
                    else:
                        retweet['getLongText'] = True
                else:
                    retweet = self.parse_weibo(retweeted_status)
                # retweet['created_at'] = self.standardize_date(
                #     retweeted_status['created_at'])
                weibo['retweet'] = retweet
            else:  # 原创
                if is_long:
                    weibo = self.get_long_weibo(weibo_id)
                    if not weibo:
                        weibo = self.parse_weibo(weibo_info)
                        weibo['getLongText'] = False
                    else:
                        weibo['getLongText'] = True
                else:
                    weibo = self.parse_weibo(weibo_info)
            # weibo['created_at'] = self.standardize_date(
            #     weibo_info['created_at'])
            return weibo
        except Exception as e:
            self.logger.log(msg=e, level=logging.ERROR)
            return None

    @staticmethod
    def is_pinned_weibo(info):
        """判断微博是否为置顶微博"""
        weibo_info = info['mblog']
        title = weibo_info.get('title')
        if title and title.get('text') == u'置顶':
            return True
        else:
            return False

    def parse_tweets(self, response):
        """the parser for user post

        Args:
            response:

        Returns:

        """
        uid = response.meta['uid']
        page = response.meta['page']
        # 检查response内容是否正确
        failed, js = 0, None
        try:
            js = json.loads(response.text)
        except Exception as e:
            failed = 1
        if not js or not js['ok'] or failed:
            self.logger.log(msg="parse tweets error:"
                                + response.url, level=logging.ERROR)
            return
        # 将当前页的所有推文入库
        cards = js['data']['cards']
        for w in cards:
            if w["card_type"] == 9:
                wb = self.get_one_weibo(w)
                if wb:
                    tweet_item = TweetItem()
                    tweet_item['_id'] = wb['id']
                    tweet_item['tweet_id'] = wb['id']
                    tweet_item['user_id'] = uid
                    tweet_item['content'] = wb
                    yield tweet_item
        # 完成该页的爬取 TODO: logging
        request_state_item = RequestStateItem()
        request_state_item['_id'] = str(uid) + '#' + str(page)
        self.page_cnt += 1
        print("[{}] {}".format(self.page_cnt, request_state_item['_id']))
        yield request_state_item

    # TODO: 1. 增量获取  2. 过滤置顶  3. 过滤转发
    # def future(self):
    #     created_at = datetime.strptime(
    #         self.standardize_date(wb['created_at']), '%Y-%m-%d')
    #     since_date = datetime.strptime(
    #         self.user_config['since_date'], '%Y-%m-%d')
    #     if created_at < since_date:
    #         if self.is_pinned_weibo(w):
    #             continue
    #         else:
    #             self.logger.info(
    #                 u'{}已获取{}({})的第{}页{}微博{}'.format(
    #                     '-' * 30, self.user['screen_name'],
    #                     self.user['id'], page,
    #                     '包含"' + self.query +
    #                     '"的' if self.query else '',
    #                     '-' * 30))
    #             return True
    #     if (not self.filter) or (
    #             'retweet' not in wb.keys()):
    #         self.weibo.append(wb)
    #         self.weibo_id_list.append(wb['id'])
    #         self.got_count += 1
    #         self.print_weibo(wb)
    #     else:
    #         self.logger.info(u'正在过滤转发微博')

    # def get_long_weibo(self, tid):
    #     """ 获取长推文（tweet_detail）
    #         对于长推文在主页api获取不全的情况，需要使用额外的接口来获取
    #     Args:
    #         tid: 推文id
    #
    #     Returns:
    #         long weibo html string
    #     """
    #     try:
    #         js = self.get_json(url=self.generate_longtext_url(tid=tid), timeout=5, max_retries=3)
    #         if js and js['ok']:
    #             return js['data']['longTextContent']
    #     except Exception as e:
    #         self.logger.log(msg="long text error: {}".format(tid), level=logging.ERROR)
    #     return None
