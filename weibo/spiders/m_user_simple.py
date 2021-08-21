#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/2/4 21:13
# @Author  : cendeavor
# @Site    : 
# @File    : m_user_simple.py
# @Software: PyCharm

# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/12/19 13:07
# @Author  : cendeavor
# @File    : cn_user.py
# @Software: PyCharm

import time
import sys
import json
from collections import OrderedDict
import scrapy
import logging
from weibo.items.m import UserItem, UserStateItem
from database_connector import MongoDBC
from scrapy.utils.project import get_project_settings

settings = get_project_settings()


class UserSpider(scrapy.Spider):
    name = 'simple_user_m'
    # allowed_domains = ['m.weibo.cn', 'weibo.com']  # crawling sites
    base_url = 'https://m.weibo.cn/'
    api = {
        'user': 'api/container/getIndex?containerid=100505',  # +uid
        'profile': {
            '0': 'api/container/getIndex?containerid=230283',
            # +uid
            '1': '_-_INFO'
        }
    }
    debug_info = {
        'user_cnt': 0
    }

    def __init__(self, *args, **kwargs):
        super(UserSpider, self).__init__(*args, **kwargs)
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
        self.cname = settings.get('MONGO_CNAME')['M_TASK']['USER']
        # self.max_weibo_cnt = settings.get('MAX_WEIBO_CNT', 500)
        # self.min_weibo_cnt = settings.get('MIN_WEIBO_CNT', 50)
        self.logger.debug('[m_user]: get task from {}'.format(self.cname))

    def generate_user_url(self, uid):
        # to generate user's osn information url
        user_info_url = self.base_url + self.api['user'] + uid
        return user_info_url

    def generate_profile_url(self, uid):
        # to generate user's profile information url
        profile_url = self.base_url + self.api['profile']['0'] + uid + self.api['profile']['1']
        return profile_url

    def start_requests(self):
        """ override
        the start of request
        Returns:

        """
        # 利用上下文管理器防止python异常终端导致游标无法清除而占用 Mongodb 资源
        with self.db[self.cname].find({
            "account_alive": {"$eq": ""},
            # "weibo_count": {"$lte": self.max_weibo_cnt, "$gte": self.min_weibo_cnt}
        }, {'_id': 1}, no_cursor_timeout=True) as uid_cursor:
            for item in uid_cursor:
                uid = item['_id']
                yield scrapy.Request(url=self.generate_user_url(uid=uid), callback=self.parse,
                                     meta={'uid': uid})
        self.dbc.close()

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

    def parse(self, response):
        """ the parser for user profile

        Args:
            response:

        Returns:

        """
        uid = response.meta['uid']

        # 用户状态
        user_state_item = UserStateItem()
        user_state_item['_id'] = uid
        user_state_item['state'] = 0
        user_state_item['profile'] = False # TODO: add in item/m.py

        try:
            info = json.loads(response.text)['data']['userInfo']
        except Exception as e:
            user_state_item['account_alive'] = False
            print('账号异常: ', uid)
            # 更新用户状态
            yield user_state_item
        else:
            user_info = OrderedDict()
            user_info['id'] = info.get('id', '')
            user_info['screen_name'] = info.get('screen_name', '')
            user_info['gender'] = info.get('gender', '')
            user_info['statuses_count'] = info.get('statuses_count', 0)
            user_info['followers_count'] = info.get('followers_count', 0)
            user_info['follow_count'] = info.get('follow_count', 0)
            user_info['description'] = info.get('description', '')
            user_info['profile_url'] = info.get('profile_url', '')
            user_info['profile_image_url'] = info.get('profile_image_url', '')
            user_info['cover_image_phone'] = info.get('cover_image_phone', '')
            user_info['avatar_hd'] = info.get('avatar_hd', '')
            user_info['urank'] = info.get('urank', 0)
            user_info['mbrank'] = info.get('mbrank', 0)
            user_info['verified'] = info.get('verified', False)
            user_info['verified_type'] = info.get('verified_type', -1)
            user_info['verified_reason'] = info.get('verified_reason', '')
            # 创建 UserItem对象
            user_item = UserItem()
            user_item['_id'] = uid
            user_item['user_id'] = uid
            user_item['content'] = self.standardize_info(user_info)
            # 更新用户状态
            user_state_item['weibo_count'] = info['statuses_count']
            user_state_item['account_alive'] = True
            user_state_item['crawled_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.debug_info['user_cnt'] += 1
            print('[{}]'.format(self.debug_info['user_cnt']), user_item['user_id'])
            yield user_item
        # 更新用户状态
        yield user_state_item
