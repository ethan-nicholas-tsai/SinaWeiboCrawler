#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 9:25
# @Author  : cendeavor
# @Site    : 
# @File    : task.py
# @Software: PyCharm

import math
from weibo.dbscripts.database_manager import MongoDBM


class TweetTaskDBM(MongoDBM):
    user_state_name = 'm_user_state'
    task_state_name = 'm_task_state'
    request_state_name = 'm_request_state'

    def __init__(self, uri, dbname, username, password):
        # 重写该类或者填充本地数据库配置信息
        super().__init__(uri, dbname, username, password)
        self.db = self.connect()
        self.user_state = self.db[self.user_state_name]
        self.task_state = self.db[self.task_state_name]
        self.request_state = self.db[self.request_state_name]

    def count_rest_task(self, min_weibo_cnt=50, max_weibo_cnt=500):
        return self.user_state.count({
            "account_alive": True,
            "state": 0,  # 0,未爬微博; 1,爬完微博; -1,在任务队列中
            "weibo_count": {"$lte": max_weibo_cnt, "$gte": min_weibo_cnt}
        })

    def count_future_task(self, quantity=10000):
        if self.task_state_name not in self.db.list_collection_names():
            return quantity
        return quantity - self.task_state.count()

    def add_tasks(self, quantity=10000, min_weibo_cnt=50, max_weibo_cnt=500):
        with self.user_state.find({
            "account_alive": True,
            "state": 0,  # 0,未爬微博; 1,爬完微博; -1,在任务队列中
            "weibo_count": {"$lte": max_weibo_cnt, "$gte": min_weibo_cnt}
        }, {
            "_id": 1, "weibo_count": 1
        }).limit(quantity) as cursor:
            for item in cursor:
                # 生成任务状态，并将任务加入任务队列
                item['state'] = '0' * int(math.ceil(item['weibo_count'] / 10.0))
                self.task_state.insert(item)
                # 更新用户推文爬取状态为正在进行（-1）
                self.user_state.update_one({"_id": item['_id']}, {"$set": {'state': -1}}, upsert=True)

    def update_tasks(self, skip=1):
        request_list = []
        uid_list = []
        task_state = {}
        # 获取本轮所有请求成功的页
        with self.request_state.find({}) as cursor:
            for item in cursor:
                request_list.append(item['_id'])
        # 获取所有执行中的任务状态
        with self.task_state.find({}, {"_id": 1, "state": 1}) as cursor:
            for item in cursor:
                task_state[item['_id']] = list(item['state'])  # 建立任务状态字典
                uid_list.append(item['_id'])  # 用作task_state的索引
        # 更新每个任务的完成页
        for it in request_list:
            uid, page = it.split('#')
            task_state[uid][-int(page)] = '1'
        cnt_done = 0
        # 清算任务
        for uid in uid_list:
            state = task_state[uid]
            is_done = True
            offset = 0
            for it in state:
                if '0' == it and offset >= skip:  # 最后一页可能就是爬不到的
                    is_done = False
                    break
                offset += 1
            # 如果完成，更新用户推文爬取状态为完成（1），同时从任务队列中删除任务
            if is_done:
                toggle_flag, nonseq_one = False, False
                for i in range(skip):
                    if state[i] == '1' and not toggle_flag:
                        toggle_flag = True
                    if state[i] == '0' and toggle_flag:
                        nonseq_one = True
                if not (toggle_flag and nonseq_one):
                    cnt_done += 1
                    print("[{}] {}".format(cnt_done, uid))
                    self.user_state.update_one({"_id": uid}, {"$set": {'state': 1}}, upsert=True)
                    self.task_state.delete_one({'_id': uid})
                else:
                    print(state)
            # 如果没有完成，更新任务完成进度(状态)
            else:
                state = ''.join(state)
                self.task_state.update_one({"_id": uid}, {"$set": {'state': state}}, upsert=True)
        # 删除本轮所有的请求成功记录
        self.request_state.delete_many({})


class LongTweetTaskDBM(MongoDBM):
    tweet_state_name = 'm_tweet'
    longtext_state_name = 'm_longtext_state'
    request_long_name = 'm_request_long'

    def __init__(self, uri, dbname, username, password):
        # 重写该类或者填充本地数据库配置信息
        super().__init__(uri, dbname, username, password)
        self.db = self.connect()
        self.tweet_state = self.db[self.tweet_state_name]
        self.task_state = self.db[self.longtext_state_name]
        self.request_state = self.db[self.request_long_name]

    def add_tasks(self, quantity=10000):
        with self.tweet_state.find({
            "content.isLongText": True,
        }, {
            "_id": 1
        }).limit(quantity) as cursor:
            cnt = 0
            for item in cursor:
                tid = item["_id"]
                # 生成任务状态，并将任务加入任务队列
                item['done'] = False
                self.task_state.update_one({"_id": tid}, {"$setOnInsert": item}, upsert=True)
                cnt += 1
                if not cnt % 1000:
                    print(cnt, end=" ", flush=True)
                if not cnt % 10000:
                    print()

    def update_tasks(self):
        request_list = []
        # 获取本轮所有请求成功的页
        with self.request_state.find({}) as cursor:
            for item in cursor:
                request_list.append(item['_id'])
        # 清算任务
        for tid in request_list:
            self.task_state.update_one({"_id": tid}, {"$set": {'done': True}}, upsert=True)
        # 删除本轮所有的请求成功记录
        self.request_state.delete_many({})


class ProfileTaskDBM(MongoDBM):
    task_state_name = 'm_user_state'
    request_state_name = 'm_request_profile'

    def __init__(self, uri, dbname, username, password):
        # 重写该类或者填充本地数据库配置信息
        super().__init__(uri, dbname, username, password)
        self.db = self.connect()
        self.task_state = self.db[self.task_state_name]
        self.request_state = self.db[self.request_state_name]

    def update_tasks(self):
        request_list = []
        # 获取本轮所有请求成功的页
        with self.request_state.find({}) as cursor:
            for item in cursor:
                request_list.append(item['_id'])
        # 清算任务
        for uid in request_list:
            self.task_state.update_one({"_id": uid}, {"$set": {'profile': True}}, upsert=True)
        # 删除本轮所有的请求成功记录
        self.request_state.delete_many({})
