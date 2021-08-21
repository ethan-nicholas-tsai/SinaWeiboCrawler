#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/17 18:58
# @Author  : cendeavor
# @Site    : 
# @File    : com_search.py
# @Software: PyCharm

import scrapy
from scrapy import Item, Field


class MetaItem(Item):
    _id = Field()  # user_id
    screen_name = Field()
    orient_type = Field()
    keyword = Field()


class WeiboItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    bid = scrapy.Field()
    user_id = scrapy.Field()
    screen_name = scrapy.Field()
    text = scrapy.Field()
    article_url = scrapy.Field()
    location = scrapy.Field()
    at_users = scrapy.Field()
    topics = scrapy.Field()
    reposts_count = scrapy.Field()
    comments_count = scrapy.Field()
    attitudes_count = scrapy.Field()
    created_at = scrapy.Field()
    source = scrapy.Field()
    pics = scrapy.Field()
    video_url = scrapy.Field()
    retweet_id = scrapy.Field()
