#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/9 16:49
# @Author  : cendeavor
# @Site    : 
# @File    : m_supertopic.py
# @Software: PyCharm

import re
from bs4 import BeautifulSoup
import requests
import scrapy
from weibo.items.m import TweetItem, TopicTweetItem, UserItem
# from weibo.items.m import StateItem
from weibo.utils.m import time_fix
import json
import time


class SuperTopicSpider(scrapy.Spider):
    name = "supertopic_m"
    allowed_domains = ['m.weibo.cn', 'weibo.com']
    base_url = 'https://m.weibo.cn/'
    api = {
        'supertopic': {'api_0': 'api/container/getIndex?containerid=',
                       # +topic_id
                       'api_1': '_-_feed',
                       'api_2': '&since_id='},
        'util': {
            'longtext_api': 'https://m.weibo.cn/statuses/extend?id=',
            'precise_time_api': 'https://m.weibo.cn/detail/'  # 其实不是api，只是通过这个链接访问特定的推文，也可把detail换成status
            # +tid(numerical)
        }
    }

    # start_urls = ["https://m.weibo.cn/api/container/getIndex?containerid=100808e056951c0679ee95c6eb872a589c0744_-_feed"]

    def __init__(self, *args, **kwargs):
        super(SuperTopicSpider, self).__init__(*args, **kwargs)
        if 'topic_id' in kwargs.keys():
            self.topic_id = kwargs['topic_id']
        else:
            self.topic_id = None
        self.cnt = 1

    @staticmethod
    def generate_supertopic_url(topic_id, since_id=None):
        url = SuperTopicSpider.base_url + SuperTopicSpider.api['supertopic']['api_0'] + topic_id + \
              SuperTopicSpider.api['supertopic']['api_1']
        if since_id:
            url = url + SuperTopicSpider.api['supertopic']['api_2'] + str(since_id)
        return url

    def start_requests(self):
        if self.topic_id:
            yield scrapy.Request(url=self.generate_supertopic_url(topic_id=self.topic_id), callback=self.parse_tweets,
                                 meta={'topic_id': self.topic_id})

    def parse_tweets(self, response):
        topic_id = response.meta['topic_id']
        data = json.loads(response.text)['data']
        cards = data['cards']
        for card in cards:
            if "card_group" in card.keys():
                card_group = card["card_group"]
                for item in card_group:
                    if item["card_type"] == '9':
                        tweet_item = TopicTweetItem()
                        tweet = item['mblog']
                        tweet_item['_id'] = tweet['id']
                        tweet_item['topic_id'] = topic_id
                        tweet_item['tweet_id'] = tweet['id']
                        tweet_item['user_id'] = tweet['user']['id']
                        user_item = UserItem()
                        user_item['content'] = tweet['user']
                        user_item['content']['topic_id'] = topic_id
                        yield user_item
                        # # 用户状态
                        # state_item = StateItem()
                        # state_item['user_id'] = tweet_item['user_id']
                        # # 更新用户状态
                        # state_item['total_num'] = tweet['user']['statuses_count']
                        # state_item['account_alive'] = True
                        # state_item['since_id'] = -1
                        # yield state_item
                        del tweet['user']
                        tweet_item['content'] = tweet
                        yield tweet_item
        next_since_id = data['pageInfo']['since_id']
        print('[{}]'.format(self.cnt), next_since_id)
        self.cnt += 1
        yield scrapy.Request(
            url=self.generate_supertopic_url(topic_id=response.meta['topic_id'], since_id=next_since_id),
            callback=self.parse_tweets)

    @staticmethod
    def extract_text(html):
        html = re.sub(r'<br />', '\n', html)
        soup = BeautifulSoup(html, "lxml")
        for a_selector in soup.find_all('a'):
            a_selector.clear()
        return soup.text.strip()

    def parse(self, response):
        """ 直接解析

        Args:
            response:

        Returns:

        """
        data = json.loads(response.text)['data']
        cards = data['cards']
        for card in cards:
            if "card_group" in card.keys():
                card_group = card["card_group"]
                for item in card_group:
                    if item["card_type"] == '9':
                        item = item["mblog"]
                        tweet_item = TweetItem()
                        tweet_item["user_id"] = item["user"]["id"]
                        tweet_item["tweet_id"] = item["id"]
                        tweet_item["user_url"] = "https://weibo.com/u/{}".format(tweet_item["user_id"])
                        tweet_item["tweet_url"] = "https://weibo.com/{}/{}".format(tweet_item["user_id"], item["bid"])
                        tweet_item["post_time"] = time_fix(item["created_at"])
                        tweet_item["repost_num"] = item["reposts_count"]
                        tweet_item["comment_num"] = item["comments_count"]
                        tweet_item["like_num"] = item["attitudes_count"]
                        if "retweeted_status" in item.keys():
                            tweet_item["is_origin"] = False
                            item = item["retweeted_status"]
                        else:
                            tweet_item["is_origin"] = True
                        # tweet_content = SuperTopicSpider.get_full_text(item["id"]) if item["isLongText"] else \
                        #     item["text"]
                        # tweet_item["location"] = BeautifulSoup(tweet_content, "lxml").find_all("span", class_="surl-text")[0].text # 不对的
                        tweet_content = item["text"]
                        tweet_item["tweet_content"] = SuperTopicSpider.extract_text(
                            tweet_content) if tweet_content else ""
                        tweet_item["image_url"] = [pic["url"] for pic in item["pics"]] if "pics" in item.keys() else []
                        tweet_item["video_url"] = item["page_info"]["page_url"] if "page_info" in item.keys() else []
                        tweet_item["crawled_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                        yield tweet_item
        next_since_id = data['pageInfo']['since_id']
        print('[{}]'.format(self.cnt), next_since_id)
        self.cnt += 1
        yield scrapy.Request(
            url=self.generate_supertopic_url(topic_id=response.meta['topic_id'], since_id=next_since_id),
            callback=self.parse)
