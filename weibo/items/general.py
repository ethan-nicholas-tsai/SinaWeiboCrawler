#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/17 18:58
# @Author  : cendeavor
# @Site    : 
# @File    : general.py
# @Software: PyCharm

from scrapy import Item, Field
import scrapy


class RelationshipItem(Item):
    """ 用户关系，只保留与关注的关系 """
    _id = Field()
    fan_id = Field()  # 关注者,即粉丝的id
    followed_id = Field()  # 被关注者的id
    crawl_time = Field()  # 抓取时间戳


class CommentItem(Item):
    """
    微博评论信息
    """
    _id = Field()
    comment_user_id = Field()  # 评论用户的id
    content = Field()  # 评论的内容
    weibo_id = Field()  # 评论的微博的url
    created_at = Field()  # 评论发表时间
    like_num = Field()  # 点赞数
    crawl_time = Field()  # 抓取时间戳
