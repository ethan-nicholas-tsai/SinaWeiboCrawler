#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/2/4 20:48
# @Author  : cendeavor
# @Site    : 
# @File    : m_user_patch.py
# @Software: PyCharm

import time
import sys
import json
from collections import OrderedDict
import scrapy
import logging
from weibo.items.m import ProfileItem, RequestProfileItem
from database_connector import MongoDBC
from scrapy.utils.project import get_project_settings

settings = get_project_settings()


class UserPatchSpider(scrapy.Spider):
    name = 'patch_user_m'
    allowed_domains = ['m.weibo.cn', 'weibo.com']  # crawling sites
    base_url = 'https://m.weibo.cn/'
    api = {
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
        super(UserPatchSpider, self).__init__(*args, **kwargs)
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
        self.max_weibo_cnt = settings.get('MAX_WEIBO_CNT', 500)
        self.min_weibo_cnt = settings.get('MIN_WEIBO_CNT', 50)
        self.logger.debug('[m_user_patch]: get task from {}'.format(self.cname))

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
            "account_alive": {"$eq": True},
            "weibo_count": {"$lte": self.max_weibo_cnt, "$gte": self.min_weibo_cnt},
            "profile": False
        }, {'_id': 1}, no_cursor_timeout=True) as uid_cursor:
            for item in uid_cursor:
                uid = item['_id']
                yield scrapy.Request(url=self.generate_profile_url(uid=uid),
                                     callback=self.parse_profile,
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

    def parse_profile(self, response):

        uid = response.meta.get('uid')

        user_info = {}

        zh_list = [
            u'生日', u'所在地', u'小学', u'初中', u'高中', u'大学', u'公司', u'注册时间',
            u'阳光信用'
        ]
        en_list = [
            'birthday', 'location', 'education', 'education', 'education',
            'education', 'company', 'registration_time', 'sunshine'
        ]
        for i in en_list:
            user_info[i] = ''

        try:
            cards = json.loads(response.text)['data']['cards']
            if isinstance(cards, list) and len(cards) > 1:
                card_list = cards[0]['card_group'] + cards[1]['card_group']
                for card in card_list:
                    if card.get('item_name') in zh_list:
                        user_info[en_list[zh_list.index(
                            card.get('item_name'))]] = card.get(
                            'item_content', '')
            request_item = RequestProfileItem()
            request_item['_id'] = uid
            yield request_item
            profile_item = ProfileItem()
            profile_item['_id'] = uid
            profile_item['content'] = self.standardize_info(user_info)
            self.debug_info['user_cnt'] += 1
            print('[{}]'.format(self.debug_info['user_cnt']), uid)
            yield profile_item
        except Exception as e:
            pass
