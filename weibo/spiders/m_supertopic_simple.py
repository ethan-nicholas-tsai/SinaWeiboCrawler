#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/2/1 11:34
# @Author  : cendeavor
# @Site    : 
# @File    : m_supertopic_simple.py
# @Software: PyCharm

import scrapy
from weibo.items.m import MetaItem
import json
from scrapy.utils.project import get_project_settings

# TODO: pipeline中的去重

class SuperTopicSpider(scrapy.Spider):
    name = "simple_supertopic_m"
    allowed_domains = ['m.weibo.cn', 'weibo.com']
    base_url = 'https://m.weibo.cn/'
    api = {
        'supertopic': {'0': 'api/container/getIndex?containerid=100808',
                       # +topic_id
                       '1': '_-_feed',
                       '2': '&since_id='},
    }

    settings = get_project_settings()
    topic_id = settings.get('TOPIC_ID')
    topic_name = settings.get('TOPIC_NAME')
    orient_type = settings.get('ORIENT_TYPE')

    cnt = 0

    # start_urls = ["https://m.weibo.cn/api/container/getIndex?containerid=100808e056951c0679ee95c6eb872a589c0744_-_feed"]

    def generate_supertopic_url(self, topic_id, since_id=None):
        url = self.base_url + self.api['supertopic']['0'] + topic_id + \
              self.api['supertopic']['1']
        if since_id:
            url = url + self.api['supertopic']['2'] + str(since_id)
        return url

    def start_requests(self):
        yield scrapy.Request(url=self.generate_supertopic_url(topic_id=self.topic_id), callback=self.parse_tweets)

    def parse_tweets(self, response):
        data = json.loads(response.text)['data']
        cards = data['cards']
        for card in cards:
            if "card_group" in card.keys():
                card_group = card["card_group"]
                for item in card_group:
                    if item["card_type"] == '9':
                        tweet = item['mblog']
                        user = tweet['user']
                        meta_item = MetaItem()
                        meta_item['_id'] = user['id']
                        meta_item['screen_name'] = user['screen_name']
                        meta_item['topic_id'] = self.topic_id
                        meta_item['topic_name'] = self.topic_name
                        meta_item['orient_type'] = self.orient_type
        next_since_id = data['pageInfo']['since_id']
        print('[{}]'.format(self.cnt), next_since_id)
        self.cnt += 1
        yield scrapy.Request(
            url=self.generate_supertopic_url(topic_id=self.topic_id, since_id=next_since_id),
            callback=self.parse_tweets)
