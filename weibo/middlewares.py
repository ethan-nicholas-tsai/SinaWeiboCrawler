# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import os
import re
import time
import json
import random
import logging
import requests
# from fake_useragent import UserAgent
# from scrapy import signals
# from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import response_status_message
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.project import get_project_settings

settings = get_project_settings()


# to add random proxy IP address for every request
class ProxyMiddleware(object):
    # 随机ip代理获取
    PROXY_POOL_URL = 'http://localhost:5555/random'

    @staticmethod
    def get_proxy():
        try:
            response = requests.get(ProxyMiddleware.PROXY_POOL_URL)
            if response.status_code == 200:
                return response.text
        except ConnectionError:
            return None

    def process_request(self, request, spider):
        request.meta['proxy'] = ProxyMiddleware.get_proxy()


# to add random user-agent for every request
class UAMiddleware(object):

    @staticmethod
    def get_ua():
        ua = random.choice(settings['USER_AGENT_LIST'])
        return ua

    def process_request(self, request, spider):
        request.headers['User-Agent'] = self.get_ua()


# TODO: cookie池
class CookieMiddleware(object):

    def __init__(self):
        pass

    @staticmethod
    def str2dict(cookie):
        cookies = dict([l.split("=", 1) for l in cookie.split("; ")])
        return cookies

    def process_request(self, request, spider):
        request.cookies = CookieMiddleware.str2dict(random.choice(settings.get('COOKIES')))


class MyRetryMiddleware(RetryMiddleware):
    """ Refer: https://blog.csdn.net/qq_33854211/article/details/78535963
    retry and check account status
    HTTP Code = 302/418 -> cookie is expired or banned, and account status will change to 'error'
    """

    def delete_proxy(self, proxy):
        if proxy:
            # delete proxy from proxies pool
            pass

    def process_response(self, request, response, spider):
        # 在之前构造的request中可以加入meta信息dont_retry来决定是否重试
        if request.meta.get('dont_retry', False):
            return response

        http_code = response.status
        reason = response_status_message(http_code)
        if http_code == 302 or http_code == 403:  # response.status in self.retry_http_codes
            spider.logger.error('RetryMiddleware: 账号异常，请检查账号是否被封或cookie是否过期')
            # self.account_collection.find_one_and_update({'_id': request.meta['account']['_id']},
            #                                             {'$set': {'status': 'error'}}, )
            # return request
            # time.sleep(random.randint(3, 5))
            return self._retry(request, reason, spider) or response
        elif http_code == 418:
            spider.logger.error('RetryLMiddleware: 代理失效，进行重试...')
            # 删除该代理
            self.delete_proxy(request.meta.get('proxy', False))
            # time.sleep(random.randint(3, 5))
            spider.logger.log(msg='RetryMiddleware: 返回值异常, 进行重试...', level=logging.WARNING)
            # 更换代理和 ua 并重试
            return self._retry(request, reason, spider) or response  # TODO: 更新since_id

        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            # 删除该代理
            self.delete_proxy(request.meta.get('proxy', False))
            # time.sleep(random.randint(3, 5))
            spider.logger.log(msg='RetryMiddleware: 连接异常, 进行重试...', level=logging.WARNING)
            # time.sleep(random.randint(1, 3))
            # 更换代理和 ua 并重试
            return self._retry(request, exception, spider)
