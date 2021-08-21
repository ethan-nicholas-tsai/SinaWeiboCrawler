#!/usr/bin/env python
# encoding: utf-8
"""
File Description: 
Author: cendeavor
Mail: nghuyong@163.com
Created Time: 2020/4/14
"""
import sys
import re
import scrapy
import traceback
from lxml import etree
from database_connector import MongoDBC
# from bs4 import BeautifulSoup
from scrapy.http import Request
import time
from weibo.items.cn import TweetItem
from weibo.utils.cn import time_fix, extract_weibo_content


class TweetSpider(scrapy.Spider):
    name = "tweet_cn"
    base_url = "https://weibo.cn"
    allowed_domains = ['weibo.cn']
    # start_urls = ["https://weibo.cn/u/1000364684?page=3"] # https://weibo.cn/isabellamydream
    # start_urls = ["https://weibo.cn/u/1506711913?page=2"]  # 基本 + 转发内容测试
    start_urls = ["https://weibo.cn/isabellamydream"]  # publish_place 和 组图测试

    def __init__(self, *args, **kwargs):
        super(TweetSpider, self).__init__(*args, **kwargs)
        if 'url' in kwargs.keys():
            self.page_url = kwargs['url']
        else:
            self.page_url = None

        if 'dbname' in kwargs.keys() and 'cname' in kwargs.keys():
            self.dbc = MongoDBC(dbname=kwargs['dbname'])
            db = self.dbc.connect()
            self.collection = db[kwargs['cname']]

        self.debug_info = {'cnt': 0}

    def deal_garbled(self, info):
        """处理乱码"""
        try:
            info = (info.xpath('string(.)').replace(u'\u200b', '').encode(
                sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
            return info
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_place(self, info):
        """获取微博发布位置"""
        try:
            div_first = info.xpath('div')[0]
            a_list = div_first.xpath('a')
            publish_place = '无'
            for a in a_list:
                if ('place.weibo.com' in a.xpath('@href')[0]
                        and a.xpath('text()')[0] == '显示地图'):
                    weibo_a = div_first.xpath("span[@class='ctt']/a")
                    if len(weibo_a) >= 1:
                        publish_place = weibo_a[-1]
                        if ('视频' == div_first.xpath(
                                "span[@class='ctt']/a/text()")[-1][-2:]):
                            if len(weibo_a) >= 2:
                                publish_place = weibo_a[-2]
                            else:
                                publish_place = u'无'
                        publish_place = self.deal_garbled(publish_place)
                        break
            # print('微博发布位置: ' + publish_place)
            return publish_place
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def extract_picture_urls(self, info, weibo_id):
        # print('开始提取图片 URL')
        """提取微博原始图片url"""
        try:
            a_list = info.xpath('./div/a/@href')
            # first_pic = 'https://weibo.cn/mblog/pic/' + weibo_id + '?rl=0'
            all_pic = 'https://weibo.cn/mblog/picAll/' + weibo_id + '?rl=1'
            # print('alist', a_list, all_pic)
            # lll = info.xpath('./div[2]/a[1]/@href')
            # if lll==:#first_pic in a_list:
            # 如果是组图
            if all_pic in a_list:
                # 先不获取
                picture_urls = info.xpath('.//a[contains(text(),"组图")]/text()')[0] + ' ' + all_pic
                # 继续发请求获取全部的图
                # selector = self.deal_html(all_pic)  # TODO: 改成scrapy格式
                # preview_picture_list = selector.xpath('//img/@src')
                # picture_list = [
                #     p.replace('/thumb180/', '/large/')
                #     for p in preview_picture_list
                # ]
                # picture_urls = ','.join(picture_list)
                # print(picture_urls)
            else:
                picture_urls = '无'
                if info.xpath('.//img/@src'):
                    preview_picture = info.xpath('.//img/@src')[-1]
                    picture_urls = preview_picture.replace(
                        '/wap180/', '/large/')
                else:
                    pass
                    # print('picture: ')
                    # print(traceback.format_exc())
                    # sys.exit(
                    #     "爬虫微博可能被设置成了'不显示图片'，请前往"
                    #     "'https://weibo.cn/account/customize/pic'，修改为'显示'"
                    # )
            return picture_urls
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_picture_urls(self, info, is_original):
        """获取微博原始图片url"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            picture_urls = {}
            if is_original:
                original_pictures = self.extract_picture_urls(info, weibo_id)
                picture_urls['tweet'] = original_pictures  # 原创图片
                picture_urls['retweet'] = '无'  # 转发图片
            else:
                retweet_url = info.xpath("div/a[@class='cc']/@href")[0]
                retweet_id = retweet_url.split('/')[-1].split('?')[0]
                retweet_pictures = self.extract_picture_urls(info, retweet_id)
                picture_urls['retweet'] = retweet_pictures  # 转发图片
                a_list = info.xpath('div[last()]/a/@href')
                original_picture = '无'
                for a in a_list:
                    if a.endswith(('.gif', '.jpeg', '.jpg', '.png')):
                        original_picture = a
                        break
                picture_urls['tweet'] = original_picture  # 原创图片
            return picture_urls
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def parse(self, response):
        tree_node = etree.HTML(response.body)
        tweet_nodes = tree_node.xpath('//div[@class="c" and @id]')
        for tweet_node in tweet_nodes:
            try:
                tweet_item = TweetItem()
                # 爬取时间
                tweet_item['crawl_time'] = int(time.time())
                # 转发链接，可获取用户id和微博id
                tweet_repost_url = tweet_node.xpath('.//a[contains(text(),"转发[")]/@href')[0]
                user_tweet_id = re.search(r'/repost/(.*?)\?uid=(\d+)', tweet_repost_url)
                # 用户id
                tweet_item['user_id'] = user_tweet_id.group(2)
                # 微博id
                tweet_item['_id'] = user_tweet_id.group(1)
                # www站微博链接
                # tweet_item['tweet_url_www'] = 'https://weibo.com/{}/{}'.format(user_tweet_id.group(2),
                #                                                            user_tweet_id.group(1))
                # wap站微博链接（含全部评论
                tweet_item['tweet_url'] = 'https://weibo.cn/comment/{}?uid={}&rl=0#cmtfrm'.format(
                    tweet_item['_id'], tweet_item['user_id'])
                # 发布时间/发布工具
                create_time_info_node = tweet_node.xpath('.//span[@class="ct"]')[-1]
                create_time_info = create_time_info_node.xpath('string(.)')
                if "来自" in create_time_info:
                    tweet_item['created_at'] = time_fix(create_time_info.split('来自')[0].strip())
                    tweet_item['publish_tool'] = create_time_info.split('来自')[1].strip()
                else:
                    tweet_item['created_at'] = time_fix(create_time_info.strip())
                # 点赞数
                like_num = tweet_node.xpath('.//a[contains(text(),"赞[")]/text()')[-1]
                tweet_item['like_num'] = int(re.search('\d+', like_num).group())
                # 转发数
                repost_num = tweet_node.xpath('.//a[contains(text(),"转发[")]/text()')[-1]
                tweet_item['repost_num'] = int(re.search('\d+', repost_num).group())
                # 评论数
                comment_num = tweet_node.xpath(
                    './/a[contains(text(),"评论[") and not(contains(text(),"原文"))]/text()')[-1]
                tweet_item['comment_num'] = int(re.search('\d+', comment_num).group())
                # 提取图片链接
                # images = tweet_node.xpath('.//img[@alt="图片"]/@src')
                # if images:
                #     tweet_item['image_url'] = images
                # 视频链接
                videos = tweet_node.xpath('.//a[contains(@href,"https://m.weibo.cn/s/video/show?object_id=")]/@href')
                if videos:
                    tweet_item['video_url'] = videos
                # 定位的经纬度信息
                map_node = tweet_node.xpath('.//a[contains(text(),"显示地图")]')
                if map_node:
                    map_node = map_node[0]
                    map_node_url = map_node.xpath('./@href')[0]
                    map_info = re.search(r'xy=(.*?)&', map_node_url).group(1)
                    tweet_item['location_map_info'] = map_info
                # 微博发布位置（和经纬度信息略微不同）
                tweet_item['publish_place'] = self.get_publish_place(tweet_node)
                # 原微博链接（只有转发微博才有）
                repost_node = tweet_node.xpath('.//a[contains(text(),"原文评论[")]/@href')
                if repost_node:
                    tweet_item['retweet_url'] = repost_node[0]
                # 是否原创
                tweet_item['is_origin'] = False if repost_node else True
                # 获取图片链接
                picture_urls = self.get_picture_urls(tweet_node, tweet_item['is_origin'])
                tweet_item['image_url'] = [picture_urls]
                # 微博内容html
                tweet_html = etree.tostring(tweet_node, encoding='unicode')
                tweet_item['html'] = tweet_html
                # 微博内容文本
                tweet_item['tweet_content'] = extract_weibo_content(tweet_html)
                all_content_link = tweet_node.xpath('.//a[text()="全文" and contains(@href,"ckAll=1")]')
                if all_content_link:  # 处理长文本，默认只有一个全文，如果是转发，只可能转发的内容为长文本（极低概率会出错）
                    all_content_url = self.base_url + all_content_link[0].xpath('./@href')[0]
                    yield Request(all_content_url, callback=self.parse_all_content, meta={'item': tweet_item},
                                  priority=1)  # priority: 优化请求顺序，值越大，请求越先被处理
                else:
                    if not tweet_item['is_origin']:
                        content = tweet_item['tweet_content']
                        retweet_content, tweet_content = content.split('转发理由:')
                        tweet_item['tweet_content'] = tweet_content.strip(' ')
                        tweet_item['retweet_content'] = retweet_content.strip(' ')
                    yield tweet_item

            except Exception as e:
                print('Error parse')
                self.logger.error(e)

    def parse_all_content(self, response):
        tree_node = etree.HTML(response.body)
        tweet_item = response.meta['item']
        content_node = tree_node.xpath('//*[@id="M_"]/div[1]')[0]
        tweet_html = etree.tostring(content_node, encoding='unicode')
        content = extract_weibo_content(tweet_html)
        if not tweet_item['is_origin']:
            tweet_item['retweet_content'] = content
            tweet_item['tweet_content'] = "".join(tweet_item['tweet_content'].split('转发理由:')[1:]).strip(' ')
        else:
            tweet_item['tweet_content'] = content
        yield tweet_item
