#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/23 0:00
# @Author  : cendeavor
# @Site    : 
# @File    : m_tweet_simple_patch.py
# @Software: PyCharm

# 1. 为修复m_tweet_simple中的longtext未获取问题
# 2. 同时考虑修复pic_num>9图片获取不全问题（需要在m_tweet_simple中增加isLongText重定义代码）
# 同时实现第二条需要更为复（难）杂（爬）的api
# 3. 如果一次没爬成功第二次爬，由于时间跨度有一天多，会导致对应的page的微博对不上（用户新发的微博把以前的微博挤到下一页去了）

import sys
import scrapy
import json
import logging
from weibo.items.m import RequestLongItem, LongTweetItem
from database_connector import MongoDBC
from scrapy.utils.project import get_project_settings

settings = get_project_settings()


class TweetPatchSpider(scrapy.Spider):
    name = 'patch_simple_tweet_m'
    allowed_domains = ['m.weibo.cn', 'weibo.com']  # crawling sites
    base_url = 'https://m.weibo.cn/'
    api = {
        'longtext': 'statuses/extend?id=',  # +tid(numerical)
    }
    request_cnt = 0

    def __init__(self, *args, **kwargs):
        super(TweetPatchSpider, self).__init__(*args, **kwargs)
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
        self.cname = settings.get('MONGO_CNAME')['M_TASK']['LONGTWEET']
        self.logger.debug('[m_tweet_patch]: get task from {}'.format(self.cname))

    def generate_longtext_url(self, tid):
        return self.base_url + self.api['longtext'] + str(tid)

    def start_requests(self):
        """ override the start of request

        Returns:

        """
        with self.db[self.cname].find({"done": False}, no_cursor_timeout=True) as cursor:
            for item in cursor:
                tid = item['_id']
                yield scrapy.Request(url=self.generate_longtext_url(tid=tid),
                                     callback=self.parse_longtext,
                                     meta={'tid': tid})
        self.dbc.close()

    def parse_longtext(self, response):
        """ 获取长推文
            对于长推文在主页api获取不全的情况，需要使用额外的接口来获取
        Args:
            response: 返回的响应

        Returns:

        """
        tid = response.meta['tid']
        try:
            js = json.loads(response.text)
            if js and js['ok']:
                longtext = js['data']['longTextContent']
                if len(longtext) > 0:
                    long_tweet_item = LongTweetItem()
                    long_tweet_item['_id'] = tid
                    long_tweet_item['text'] = longtext
                    yield long_tweet_item
                    request_long_item = RequestLongItem()
                    request_long_item['_id'] = tid
                    self.request_cnt += 1
                    print("[{}] {}".format(self.request_cnt, tid))
                    yield request_long_item
                else:
                    self.logger.log(msg="[{}]: length not match!".format(tid), level=logging.ERROR)
        except Exception as e:
            if "<!DOCTYPE html>" in response.text:
                self.logger.log(msg="long text parse error: {}".format(response.url), level=logging.ERROR)
            else:
                self.logger.log(msg="long text not found", level=logging.ERROR)
