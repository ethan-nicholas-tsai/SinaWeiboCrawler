#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/17 19:01
# @Author  : cendeavor
# @Site    : 
# @File    : cn.py
# @Software: PyCharm

from scrapy import Item, Field


class UserItem(Item):
    """ User Information"""
    _id = Field()  # 用户ID
    nick_name = Field()  # 昵称
    gender = Field()  # 性别
    province = Field()  # 所在省
    city = Field()  # 所在城市
    brief_introduction = Field()  # 简介
    birthday = Field()  # 生日
    tweets_num = Field()  # 微博数
    follows_num = Field()  # 关注数
    fans_num = Field()  # 粉丝数
    sex_orientation = Field()  # 性取向
    sentiment = Field()  # 感情状况
    vip_level = Field()  # 会员等级
    authentication = Field()  # 认证
    person_url = Field()  # 首页链接
    labels = Field()  # 标签
    # added by cyc
    avatar = Field()  # 头像
    education = Field()  # 学习经历
    work = Field()  # 工作经历
    crawl_time = Field()  # 抓取时间戳


class TweetItem(Item):
    """Tweet information """
    _id = Field()  # 微博id
    user_id = Field()  # 发表该微博用户的id
    is_origin = Field()  # 是否原创
    tweet_url = Field()  # 微博链接
    # tweet_url_www = Field()  # www站微博链接
    retweet_url = Field()  # 原始微博链接，只有转发的微博才有这个字段
    created_at = Field()  # 微博发表时间
    location_map_info = Field()  # 定位的经纬度信息
    publish_place = Field()  # 发表地点
    publish_tool = Field()  # 发布微博的工具
    like_num = Field()  # 点赞数
    repost_num = Field()  # 转发数
    comment_num = Field()  # 评论数
    html = Field()  # 微博html
    tweet_content = Field()  # 原创内容
    retweet_content = Field()  # 转发内容
    image_url = Field()  # 图片
    # tweet_pics_url = Field()  # 原创图片
    # retweet_pics_url = Field()  # 转发图片
    video_url = Field()  # 视频
    crawl_time = Field()  # 抓取时间戳


class UserStateItem(Item):
    """ User Information"""
    _id = Field()  # 用户ID
    account_alive = Field(default="")  # 是否存活
    page_num = Field()


class UrlItem(Item):
    """ Url """
    user_id = Field()  # 用户ID
    page_url = Field()  # url
    state = Field(default=False)  # 是否被爬取
