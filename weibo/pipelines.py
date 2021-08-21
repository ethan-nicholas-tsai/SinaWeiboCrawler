# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
import copy

from weibo.items import general, cn, m, com
from database_connector import MongoDBC
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings

settings = get_project_settings()


class MongoPipeline(object):

    def __init__(self):
        # to check the __uid from TotalNumItem, means just need to save one item and drop others
        self.dbc = MongoDBC(
            uri=settings.get('MONGO_URI'),
            dbname=settings.get('MONGO_DATABASE'),
            username=settings.get('MONGO_USER'),
            password=settings.get('MONGO_PASSWORD')
        )
        self.db = self.dbc.connect()
        self.collection = self.db['weibo']
        self.CNUserStates = self.db['cn_user_state']
        self.CNUrls = self.db['cn_url']
        self.CNUsers = self.db["cn_user"]
        self.CNTweets = self.db["cn_tweet"]
        self.MUsers = self.db["m_user"]
        self.MProfiles = self.db["m_profile"]
        self.MTweets = self.db["m_tweet"]
        self.MUserStates = self.db["m_user_state"]
        self.MRequestProfile = self.db["m_request_profile"]
        self.MRequestStates = self.db['m_request_state']
        self.MRequestLong = self.db['m_request_long']
        self.MLongTweets = self.db['m_long_tweet']
        self.MTopicTweets = self.db["m_topic_tweet"]
        self.COMMetas = self.db['com_meta']
        self.Comments = self.db["comment"]
        self.Relationships = self.db["relationship"]

    def close_spider(self, spider):
        self.dbc.close()

    def process_item(self, item, spider):
        from pymongo.errors import ServerSelectionTimeoutError

        try:
            if isinstance(item, cn.UrlItem):
                self.CNUrls.update({'page_url': item['page_url']}, {'$set': dict(item)}, upsert=True)
            elif isinstance(item, cn.UserStateItem):
                self.insert_item(self.CNUserStates, item)
            elif isinstance(item, cn.UserItem):
                self.insert_item(self.CNUsers, item)
            elif isinstance(item, cn.TweetItem):
                self.insert_item(self.CNTweets, item)
            elif isinstance(item, com.MetaItem):
                self.insert_item(self.COMMetas, item)
            elif 'keyword' in item.keys() and 'weibo' in item.keys():
                new_item = copy.deepcopy(item)
                if not self.collection.find_one({'id': new_item['weibo']['id']}):
                    self.collection.insert_one(dict(new_item['weibo']))
                else:
                    self.collection.update_one({'id': new_item['weibo']['id']},
                                               {'$set': dict(new_item['weibo'])})
            elif isinstance(item, m.UserItem):
                self.insert_item(self.MUsers, item)
            elif isinstance(item, m.ProfileItem):
                self.MProfiles.insert_one(dict(item))
            elif isinstance(item, m.TweetItem):
                self.MTweets.insert_one(dict(item))  # 需要考虑会不会重复！（应该不会）
                # self.insert_item(self.MTweets, item)
            elif isinstance(item, m.UserStateItem):
                self.insert_item(self.MUserStates, item)
            elif isinstance(item, m.RequestProfileItem):
                self.MRequestProfile.insert_one(dict(item))
            elif isinstance(item, m.RequestStateItem):
                self.MRequestStates.insert_one(dict(item))  # 反正都会删掉，不需要upsert
                # self.insert_item(self.MRequestStates, item)
            elif isinstance(item, m.RequestLongItem):
                self.MRequestLong.insert_one(dict(item))
            elif isinstance(item, m.LongTweetItem):
                self.MLongTweets.insert_one(dict(item))
            elif isinstance(item, m.TopicTweetItem):
                self.insert_item(self.MTopicTweets, item)
            elif isinstance(item, m.HotSearchItem):
                insert_dic = {'content': item['hot_search'], 'time_stamp': item['time_stamp']}
                self.db['m_hot_search'].update({'time_stamp': item['time_stamp']},
                                               {'$set': insert_dic}, upsert=True)
            elif isinstance(item, m.FansListItem):
                self.db['m_followers'].insert_one(dict(item))
            elif isinstance(item, m.FollowsListItem):
                self.db['m_follows'].insert_one(dict(item))
            elif isinstance(item, m.KeyWordsItem):
                item_dict = dict(item)
                self.db['m_key_words'].update_one({'post.id': item_dict['post']['id']}, {'$set': item_dict},
                                                  upsert=True)
            return item

        except ServerSelectionTimeoutError:
            spider.pymongo_error = True  # 在search_spider中的变量，用于检查环境是否配好

    @staticmethod
    def insert_item(collection, item):
        collection.update({'_id': item['_id']}, {'$set': dict(item)}, upsert=True)


class DuplicatesPipeline(object):
    def __init__(self):
        # 特定需求程序变量
        meta_only = settings.get('META_ONLY', False)  # 是否仅捕获元数据 {user_id, screen_name}
        if meta_only:
            self.ids_seen = set(self.get_meta_ids())
        else:
            self.ids_seen = set()

    def process_item(self, item, spider):
        if 'weibo' in item.keys() and 'keyword' in item.keys():
            if item['weibo']['id'] in self.ids_seen:
                raise DropItem("过滤重复微博: %s" % item)
            else:
                self.ids_seen.add(item['weibo']['id'])
                return item
        elif '_id' in dict(item).keys() and isinstance(item, com.MetaItem):  # or isinstance(item, cn.TweetItem)
            if item['_id'] in self.ids_seen:
                raise DropItem("过滤重复微博: %s" % item)
            else:
                self.ids_seen.add(item['_id'])
                return item
        else:
            return item

    @staticmethod
    def get_meta_ids():
        dbc_id = MongoDBC(
            uri=settings.get('MONGO_URI'),
            dbname=settings.get('MONGO_DATABASE'),
            username=settings.get('MONGO_USER'),
            password=settings.get('MONGO_PASSWORD')
        )
        db_id = dbc_id.connect()
        user_id_list = []
        cname = 'com_meta'
        if cname in db_id.list_collection_names():
            with db_id[cname].find({}, {"_id": 1}) as cursor:
                for item in cursor:
                    user_id_list.append(item['_id'])
        dbc_id.close()
        return user_id_list
