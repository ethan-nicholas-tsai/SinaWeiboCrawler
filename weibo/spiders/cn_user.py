"""
File Description:
Author: cendeavor
Mail: nghuyong@163.com
Created Time: 2020/4/14
"""
import re
from lxml import etree
import time
from database_connector import MongoDBC
from scrapy import Selector
from scrapy.http import Request
from scrapy import Spider
from weibo.items.cn import UserItem, UserStateItem, UrlItem
from weibo.utils.util import Colored


class UserSpider(Spider):
    name = "user_cn"
    base_url = "https://weibo.cn"
    allowed_domains = ['weibo.cn', 'weibo.com']

    def __init__(self, *args, **kwargs):
        super(UserSpider, self).__init__(*args, **kwargs)
        if 'uid' in kwargs.keys():
            self.__uid = kwargs['uid']
        else:
            self.__uid = None

        if 'dbname' in kwargs.keys() and 'cname' in kwargs.keys():
            self.dbc = MongoDBC(dbname=kwargs['dbname'])
            db = self.dbc.connect()
            self.collection = db[kwargs['cname']]

        self.debug_info = {'cnt': 0}

    def start_requests(self):
        if self.collection:
            # 利用上下文管理器防止python异常终端导致游标无法清除而占用 Mongodb 资源
            with self.collection.find({"account_alive": {"$eq": ""}},
                                      {'_id': 1},
                                      no_cursor_timeout=True) as uid_cursor:
                for item in uid_cursor:
                    uid = item['_id']
                    yield Request(url=self.base_url + '/{}/info'.format(uid), callback=self.parse)
            self.dbc.close()
        elif self.__uid:
            yield Request(url=self.base_url + '/{}/info'.format(self.__uid), callback=self.parse)

    def parse(self, response):
        user_item = UserItem()
        user_item['crawl_time'] = int(time.time())
        uid = re.findall('(\d+)/info', response.url)[0]
        try:
            selector = Selector(response)
        except Exception as e:
            self.debug_info['cnt'] += 1
            print(Colored.red('[{}] {}'.format(self.debug_info['cnt'], uid)))
            user_state_item = UserStateItem()
            user_state_item['_id'] = uid
            user_state_item['account_alive'] = False
            return user_state_item
        # 检查cookie是否过期
        cookie_status = selector.xpath('//title/text()')[0].extract()[:-3]
        if cookie_status == '登录 - 新' or cookie_status == '新浪':
            print('cookie错误或已过期')
            print(Colored.red('[-] {}'.format(uid)))
            user_state_item = UserStateItem()
            user_state_item['_id'] = uid
            user_state_item['account_alive'] = False
            return user_state_item
        # 提取用户信息
        user_item['_id'] = uid
        user_info_text = ";".join(selector.xpath('body/div[@class="c"]//text()').extract())
        nick_name = re.findall('昵称;?:?(.*?);', user_info_text)
        gender = re.findall('性别;?:?(.*?);', user_info_text)
        place = re.findall('地区;?:?(.*?);', user_info_text)
        brief_introduction = re.findall('简介;?:?(.*?);', user_info_text)
        birthday = re.findall('生日;?:?(.*?);', user_info_text)
        sex_orientation = re.findall('性取向;?:?(.*?);', user_info_text)
        sentiment = re.findall('感情状况;?:?(.*?);', user_info_text)
        vip_level = re.findall('会员等级;?:?(.*?);', user_info_text)
        authentication = re.findall('认证;?:?(.*?);', user_info_text)
        labels = re.findall('标签;?:?(.*?)更多>>', user_info_text)
        if nick_name and nick_name[0]:
            user_item["nick_name"] = nick_name[0].replace(u"\xa0", "")
        if gender and gender[0]:
            user_item["gender"] = gender[0].replace(u"\xa0", "")
        if place and place[0]:
            place = place[0].replace(u"\xa0", "").split(" ")
            user_item["province"] = place[0]
            if len(place) > 1:
                user_item["city"] = place[1]
        if brief_introduction and brief_introduction[0]:
            user_item["brief_introduction"] = brief_introduction[0].replace(u"\xa0", "")
        if birthday and birthday[0]:
            user_item['birthday'] = birthday[0]
        if sex_orientation and sex_orientation[0]:
            if sex_orientation[0].replace(u"\xa0", "") == gender[0]:
                user_item["sex_orientation"] = "同性恋"
            else:
                user_item["sex_orientation"] = "异性恋"
        if sentiment and sentiment[0]:
            user_item["sentiment"] = sentiment[0].replace(u"\xa0", "")
        if vip_level and vip_level[0]:
            user_item["vip_level"] = vip_level[0].replace(u"\xa0", "")
        if authentication and authentication[0]:
            user_item["authentication"] = authentication[0].replace(u"\xa0", "")
        if labels and labels[0]:
            user_item["labels"] = labels[0].replace(u"\xa0", ",").replace(';', '').strip(',')
        # Added by cyc
        selector = etree.HTML(response.body)
        avatar = selector.xpath("//div[@class='c']/img/@src")  # 头像
        if avatar and avatar[0]:
            user_item['avatar'] = avatar[0]
        # 工作或学习经历
        other_info = selector.xpath("//div[@class='tip'][2]/text()")
        if other_info:
            if other_info[0] == u'学习经历':
                user_item['education'] = selector.xpath(
                    "//div[@class='c'][4]/text()")[0][1:].replace(
                    u'\xa0', u' ')
                work = selector.xpath("//div[@class='tip'][3]/text()")
                if work and work[0] == u'工作经历':
                    user_item['work'] = selector.xpath(
                        "//div[@class='c'][5]/text()")[0][1:].replace(
                        u'\xa0', u' ')
            elif other_info[0] == u'工作经历':
                user_item['work'] = selector.xpath(
                    "//div[@class='c'][4]/text()")[0][1:].replace(
                    u'\xa0', u' ')

        request_meta = response.meta
        request_meta['item'] = user_item
        yield Request(self.base_url + '/u/{}'.format(user_item['_id']),
                      callback=self.parse_further_information,
                      meta=request_meta, dont_filter=True, priority=1)

    def parse_further_information(self, response):
        text = response.text
        user_item = response.meta['item']
        tweets_num = re.findall('微博\[(\d+)\]', text)
        if tweets_num:
            user_item['tweets_num'] = int(tweets_num[0])
        follows_num = re.findall('关注\[(\d+)\]', text)
        if follows_num:
            user_item['follows_num'] = int(follows_num[0])
        fans_num = re.findall('粉丝\[(\d+)\]', text)
        if fans_num:
            user_item['fans_num'] = int(fans_num[0])
        yield user_item

        self.debug_info['cnt'] += 1
        # 获取微博页数
        all_page = re.search(r'/>&nbsp;1/(\d+)页</div>', text)
        if all_page:
            all_page = all_page.group(1)
            all_page = int(all_page)
        # 只对微博数小于1000的用户生成url，超过了就大概率不是抑郁症了，且爬取体量太大，可以在后续作为补充数据集
        if not tweets_num:
            print('[{}] {}, 0'.format(self.debug_info['cnt'], user_item['_id']))
        elif user_item['tweets_num'] < 1000:
            if all_page:
                for page_num in range(1, all_page + 1):
                    page_url = response.url + '?page=' + str(page_num)
                    url_item = UrlItem()
                    url_item['user_id'] = user_item['_id']
                    url_item['page_url'] = page_url
                    url_item['state'] = False
                    yield url_item
                print(Colored.green('[{}] {}, {}'.format(self.debug_info['cnt'], user_item['_id'], all_page)))
        else:
            print('[{}] {}, {}'.format(self.debug_info['cnt'], user_item['_id'], user_item['tweets_num']))

        # 更新用户状态
        user_state_item = UserStateItem()
        user_state_item['_id'] = user_item['_id']
        user_state_item['account_alive'] = True
        user_state_item['page_num'] = all_page if all_page else 0
        yield user_state_item
