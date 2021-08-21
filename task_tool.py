#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/2/4 22:50
# @Author  : cendeavor
# @Site    : 
# @File    : task_tool.py
# @Software: PyCharm


def update_tweet_task(dbname, skip=1):
    from weibo.dbscripts.m.task import TweetTaskDBM
    from weibo.settings import MONGO_URI, MONGO_DATABASE, MONGO_USER, MONGO_PASSWORD

    # 清算爬虫任务
    task_dbm = TweetTaskDBM(
        uri=MONGO_URI,
        dbname=dbname,
        username=MONGO_USER,
        password=MONGO_PASSWORD
    )
    task_dbm.update_tasks(skip=skip)
    task_dbm.close()


def add_longtext_task(dbname):
    from weibo.dbscripts.m.task import LongTweetTaskDBM
    from weibo.settings import MONGO_URI, MONGO_DATABASE, MONGO_USER, MONGO_PASSWORD

    task_dbm = LongTweetTaskDBM(
        uri=MONGO_URI,
        dbname=dbname,
        username=MONGO_USER,
        password=MONGO_PASSWORD
    )
    task_dbm.add_tasks(
        quantity=0,  # task_num, 0表示全部添加
    )
    task_dbm.close()


def update_profile_task(dbname):
    from weibo.dbscripts.m.task import ProfileTaskDBM
    from weibo.settings import MONGO_URI, MONGO_DATABASE, MONGO_USER, MONGO_PASSWORD

    # 清算爬虫任务
    task_dbm = ProfileTaskDBM(
        uri=MONGO_URI,
        dbname=dbname,
        username=MONGO_USER,
        password=MONGO_PASSWORD
    )
    task_dbm.update_tasks()
    task_dbm.close()


def recover_profile_task(dbname):
    # TODO: 如果registration_time为''则重置user_state_item中的profile为false
    pass


if __name__ == '__main__':
    # add_longtext_task(dbname="control_weibo")
    # update_profile_task(dbname="mdd_weibo")
    update_tweet_task(dbname="mdd_weibo", skip=3)
