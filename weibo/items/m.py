#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/17 19:01
# @Author  : cendeavor
# @Site    : 
# @File    : m.py
# @Software: PyCharm

import scrapy
from scrapy import Item, Field


class MetaItem(Item):
    _id = Field()  # user_id
    screen_name = Field()
    orient_type = Field()
    topic_id = Field()
    topic_name = Field()


class TopicTweetItem(scrapy.Item):
    _id = scrapy.Field()
    topic_id = scrapy.Field()
    tweet_id = scrapy.Field()
    user_id = scrapy.Field()
    content = scrapy.Field()


class UserItem(scrapy.Item):
    _id = scrapy.Field()
    user_id = scrapy.Field()
    content = scrapy.Field()


class ProfileItem(scrapy.Item):
    _id = scrapy.Field()
    content = scrapy.Field()


class TweetItem(scrapy.Item):
    _id = scrapy.Field()
    tweet_id = scrapy.Field()
    user_id = scrapy.Field()
    content = scrapy.Field()


class LongTweetItem(scrapy.Item):
    _id = scrapy.Field()
    text = scrapy.Field()


class UserStateItem(scrapy.Item):
    _id = scrapy.Field()  # 用户id
    account_alive = Field()  # 用户账号是否存活
    state = scrapy.Field()  # 0,未爬微博; 1,爬完微博; -1,在任务队列中
    weibo_count = scrapy.Field()  # 用户微博数
    crawled_time = scrapy.Field()  # 最后一次爬取该用户的时间


class TaskStateItem(scrapy.Item):
    _id = scrapy.Field()  # 用户id
    weibo_count = Field()  # 用户微博数
    state = scrapy.Field()  # 记录用户每页是否爬到, 01序列字符串
    done = scrapy.Field()  # 是否完成任务


class LongTextStateItem(scrapy.Item):
    _id = scrapy.Field()  # 推文id
    done = scrapy.Field()  # 是否完成任务


class RequestProfileItem(scrapy.Item):
    _id = scrapy.Field()


class RequestStateItem(scrapy.Item):
    _id = scrapy.Field()  # 用户id加页数（_id#page格式）


class RequestLongItem(scrapy.Item):
    _id = scrapy.Field()  # 推文id


class HotSearchItem(scrapy.Item):
    # Item for real time hot search information
    hot_search = scrapy.Field()
    time_stamp = scrapy.Field()


class FansListItem(scrapy.Item):
    uid = scrapy.Field()
    fans_list = scrapy.Field()


class FollowsListItem(scrapy.Item):
    uid = scrapy.Field()
    follows_list = scrapy.Field()


class KeyWordsItem(scrapy.Item):
    key_words = scrapy.Field()
    is_crawled = scrapy.Field()
    post = scrapy.Field()


class FailedUrlItem(scrapy.Item):
    uid = scrapy.Field()
    url = scrapy.Field()
