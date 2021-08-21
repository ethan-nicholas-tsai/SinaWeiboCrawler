# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 20:26
# @Author  : cendeavor
# @Site    : 
# @File    : com_search_simple.py
# @Software: PyCharm

import os
import re
import sys
from time import sleep
import random
from datetime import datetime, timedelta
from urllib.parse import unquote
import logging
import scrapy
import weibo.utils.util as util
from scrapy.exceptions import CloseSpider
from scrapy.utils.project import get_project_settings
from weibo.items.com import WeiboItem, MetaItem


class SearchSpider(scrapy.Spider):
    name = 'simple_search_com'
    allowed_domains = ['weibo.com']
    base_url = 'https://s.weibo.com'

    settings = get_project_settings()
    keyword_list = settings.get('KEYWORD_LIST')
    if not isinstance(keyword_list, list):
        if not os.path.isabs(keyword_list):
            keyword_list = os.getcwd() + os.sep + keyword_list
        if not os.path.isfile(keyword_list):
            sys.exit('不存在%s文件' % keyword_list)
        keyword_list = util.get_keyword_list(keyword_list)
    # 配置搜索条件
    for i, keyword in enumerate(keyword_list):
        if len(keyword) > 2 and keyword[0] == '#' and keyword[-1] == '#':
            keyword_list[i] = '%23' + keyword[1:-1] + '%23'
    weibo_type = util.convert_weibo_type(settings.get('WEIBO_TYPE'))
    contain_type = util.convert_contain_type(settings.get('CONTAIN_TYPE'))
    regions = util.get_regions(settings.get('REGION'))
    # 配置时间
    start_date = settings.get('START_DATE',
                              datetime.now().strftime('%Y-%m-%d'))  # 默认值为当前时间
    end_date = settings.get('END_DATE', datetime.now().strftime('%Y-%m-%d'))
    if util.str_to_time(start_date) > util.str_to_time(end_date):
        sys.exit('settings.py配置错误，START_DATE值应早于或等于END_DATE值，请重新配置settings.py')
    start_time = settings.get('START_TIME', '0')  # 默认起始时间为0点
    end_time = settings.get('END_TIME', '0')  # 默认结束时间为0点
    if not isinstance(start_time, list) and start_time > end_time:
        sys.exit('settings.py配置错误, START_TIME值应该小于等于END_TIME值，请重新配置settings.py')
    if isinstance(start_time, list):
        if not isinstance(end_time, list) or len(start_time) != len(end_time):
            sys.exit('settings.py配置错误, START_TIME和END_TIME应为长度相同的列表')
        for i in range(len(start_time)):
            if start_time[i] > end_time[i]:
                sys.exit('settings.py配置错误, START_TIME和END_TIME每个位置都应为小于关系: 第{}个错误！'.format(i))
    # 配置自动细分
    further_threshold = settings.get('FURTHER_THRESHOLD', 46)  # 默认值为当前时间
    # 用于检查环境是否配好：check_environment(self)
    mongo_error = False
    pymongo_error = False
    # 特定需求程序变量
    user_type = settings.get('USER_TYPE')
    meta_only = settings.get('META_ONLY', False)  # 是否仅捕获元数据 {user_id, screen_name}
    debug_cnt = 0
    request_num = 0

    def start_requests(self):
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(self.end_date,
                                     '%Y-%m-%d') + timedelta(days=1)
        start_date_str = start_date.strftime('%Y-%m-%d')  # 正式的时间格式还需加上"-0",其中0可被替换成0~23
        end_date_str = end_date.strftime('%Y-%m-%d')
        # 生成最终的url
        for keyword in self.keyword_list:
            if not self.settings.get('REGION') or '全部' in self.settings.get(
                    'REGION'):
                base_url = 'https://s.weibo.com/weibo?q=%s' % keyword
                url = base_url + self.weibo_type
                url += self.contain_type
                # 处理时间条件
                if not isinstance(self.start_time, list):
                    # 开始日期到终止日期全部爬取
                    if self.start_time == '0' and self.end_time == '0':
                        for date_str in util.iter_date(start_date_str, end_date_str, day_gap=1, reverse=True):
                            target_url = url + '&timescope=custom:{}:{}'.format(date_str, date_str)
                            yield scrapy.Request(url=target_url,
                                                 callback=self.parse,
                                                 meta={
                                                     'base_url': base_url,
                                                     'keyword': keyword,
                                                 }, dont_filter=True)
                    # 按照单一时间段爬取
                    else:
                        for date_str in util.iter_date(start_date_str, end_date_str, day_gap=1, reverse=True):
                            start_str = date_str + '-' + self.start_time
                            end_str = date_str + '-' + self.end_time
                            target_url = url + '&timescope=custom:{}:{}'.format(start_str, end_str)
                            yield scrapy.Request(url=target_url,
                                                 callback=self.parse,
                                                 meta={
                                                     'base_url': base_url,
                                                     'keyword': keyword,
                                                 }, dont_filter=True)

    def parse(self, response):
        keyword = response.meta.get('keyword')
        is_empty = response.xpath(
            '//div[@class="card card-no-result s-pt20b40"]')
        page_count = len(response.xpath('//ul[@class="s-scroll"]/li'))
        if is_empty:
            print('当前页面搜索结果为空')
        else:
            # 搜索结果页数适中，直接爬取
            if self.meta_only:
                for meta_item in self.parse_meta(response):
                    yield meta_item
                self.debug_cnt += 1
                print('[{}]: '.format(self.debug_cnt) + response.url)
                for page in range(2, page_count + 1):
                    yield scrapy.Request(url=response.url + '&page=' + str(page),
                                         callback=self.parse_page,
                                         meta={'keyword': keyword}, priority=1, dont_filter=True)

    def parse_page(self, response):
        """解析一页搜索结果的信息"""
        keyword = response.meta.get('keyword')
        is_empty = response.xpath(
            '//div[@class="card card-no-result s-pt20b40"]')
        if is_empty:
            print('当前页面搜索结果为空')
        else:
            if self.meta_only:
                for meta_item in self.parse_meta(response):
                    yield meta_item
                self.debug_cnt += 1
                print('[{}]: '.format(self.debug_cnt) + response.url)

    def parse_meta(self, response):
        """解析网页中的微博信息"""
        keyword = response.meta.get('keyword')
        for sel in response.xpath("//div[@class='card-wrap']"):
            info = sel.xpath(
                "div[@class='card']/div[@class='card-feed']/div[@class='content']/div[@class='info']"
            )
            if info:
                meta_item = MetaItem()
                meta_item['_id'] = info[0].xpath(
                    'div[2]/a/@href').extract_first().split('?')[0].split(
                    '/')[-1]
                meta_item['screen_name'] = info[0].xpath(
                    'div[2]/a/@nick-name').extract_first()
                meta_item['orient_type'] = self.user_type
                meta_item['keyword'] = keyword.replace("%23", "#")
                # self.logger.log(msg=meta_item, level=logging.INFO)
                yield meta_item
