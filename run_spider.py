# -*- coding: utf-8 -*-
# @Author  : cendeavor
# @Time    : 2021/1/19 16:25
# @Function: function for calling the crawler

import os
import sys
import multiprocessing
from scrapy.cmdline import execute


def crawl_search():
    cmd = f"scrapy crawl search_com"
    execute(cmd.split())


def crawl_search_simple():
    cmd = f"scrapy crawl simple_search_com"
    execute(cmd.split())


def crawl_user():
    cmd = f"scrapy crawl user_m"
    execute(cmd.split())


def crawl_profile():
    from weibo.dbscripts.m.task import ProfileTaskDBM
    from weibo.settings import MONGO_URI, MONGO_DATABASE, MONGO_USER, MONGO_PASSWORD

    while True:
        # 开始爬虫任务
        cmd = f"scrapy crawl patch_user_m"
        # execute(cmd.split())  # 只能执行一次
        os.system(cmd)  # pycharm终端有时候会出现 sh: 1: scrapy: not found
        # 清算爬虫任务
        task_dbm = ProfileTaskDBM(
            uri=MONGO_URI,
            dbname=MONGO_DATABASE,
            username=MONGO_USER,
            password=MONGO_PASSWORD
        )
        task_dbm.update_tasks()
        task_dbm.close()


def crawl_tweet():
    from weibo.dbscripts.m.task import TweetTaskDBM
    from weibo.settings import MONGO_URI, MONGO_DATABASE, MONGO_USER, MONGO_PASSWORD
    from weibo.settings import MIN_WEIBO_CNT, MAX_WEIBO_CNT, TASK_NUM_PER_ROUND

    max_weibo_cnt = MAX_WEIBO_CNT
    min_weibo_cnt = MIN_WEIBO_CNT
    task_num = TASK_NUM_PER_ROUND

    while True:
        # TODO: 如何成批喂入任务，且不导致一些死任务反复被执行且残留任务队列，同时将死任务从任务队列删除时，还需保留其状态
        # 其实，m_tweet_simple的代码逻辑无需批量喂入任务，因为两类item都是insert进入的，且任务数其实挺少，不是百万级别的，upsert不碍事
        # TODO: 只需将此处代码逻辑变成一次添加全部任务，且提出while循环即可
        # task_dbm = TweetTaskDBM(
        #     uri=MONGO_URI,
        #     dbname=MONGO_DATABASE,
        #     username=MONGO_USER,
        #     password=MONGO_PASSWORD
        # )
        # # 如果没有任务就退出
        # rest_cnt = task_dbm.count_rest_task(
        #     min_weibo_cnt=min_weibo_cnt,
        #     max_weibo_cnt=max_weibo_cnt
        # )
        # print("*"*40)
        # print("[Rest Task]: ", rest_cnt)
        # if not rest_cnt:
        #     task_dbm.close()
        #     break
        # # 添加爬虫任务
        # task_cnt = task_dbm.count_future_task(quantity=task_num)
        # print("[Future Task]: ", task_cnt)
        # if task_cnt >  0:
        #     task_dbm.add_tasks(
        #         quantity=0,  # task_num, 0表示全部添加
        #         min_weibo_cnt=min_weibo_cnt,
        #         max_weibo_cnt=max_weibo_cnt
        #     )
        # task_dbm.close()
        # 开始爬虫任务
        cmd = f"scrapy crawl simple_tweet_m"
        # execute(cmd.split())
        os.system(cmd)
        # 清算爬虫任务
        task_dbm = TweetTaskDBM(
            uri=MONGO_URI,
            dbname=MONGO_DATABASE,
            username=MONGO_USER,
            password=MONGO_PASSWORD
        )
        task_dbm.update_tasks()
        task_dbm.close()


def crawl_tweet_simple():
    from weibo.dbscripts.m.task import TweetTaskDBM
    from weibo.settings import MONGO_URI, MONGO_DATABASE, MONGO_USER, MONGO_PASSWORD
    from weibo.settings import MIN_WEIBO_CNT, MAX_WEIBO_CNT

    # max_weibo_cnt = MAX_WEIBO_CNT
    # min_weibo_cnt = MIN_WEIBO_CNT
    #
    # task_dbm = TweetTaskDBM(
    #     uri=MONGO_URI,
    #     dbname=MONGO_DATABASE,
    #     username=MONGO_USER,
    #     password=MONGO_PASSWORD
    # )
    # task_dbm.add_tasks(
    #     quantity=0,  # task_num, 0表示全部添加
    #     min_weibo_cnt=min_weibo_cnt,
    #     max_weibo_cnt=max_weibo_cnt
    # )
    # task_dbm.close()
    # 爬
    while True:
        # 开始爬虫任务
        cmd = f"scrapy crawl simple_tweet_m"
        # execute(cmd.split())
        os.system(cmd)
        # 清算爬虫任务
        task_dbm = TweetTaskDBM(
            uri=MONGO_URI,
            dbname=MONGO_DATABASE,
            username=MONGO_USER,
            password=MONGO_PASSWORD
        )
        task_dbm.update_tasks(skip=3)
        task_dbm.close()


def crawl_longtext():
    from weibo.dbscripts.m.task import LongTweetTaskDBM
    from weibo.settings import MONGO_URI, MONGO_DATABASE, MONGO_USER, MONGO_PASSWORD

    # task_dbm = LongTweetTaskDBM(
    #     uri=MONGO_URI,
    #     dbname=MONGO_DATABASE,
    #     username=MONGO_USER,
    #     password=MONGO_PASSWORD
    # )
    # task_dbm.add_tasks(
    #     quantity=0,  # task_num, 0表示全部添加
    # )
    # task_dbm.close()

    while True:
        # 开始爬虫任务
        cmd = f"scrapy crawl patch_simple_tweet_m"
        # execute(cmd.split())
        os.system(cmd)
        # 清算爬虫任务
        task_dbm = LongTweetTaskDBM(
            uri=MONGO_URI,
            dbname=MONGO_DATABASE,
            username=MONGO_USER,
            password=MONGO_PASSWORD
        )
        task_dbm.update_tasks()
        task_dbm.close()


if __name__ == '__main__':
    # crawl_search()
    # crawl_search_simple()
    # crawl_user()
    # crawl_profile()
    # crawl_tweet()
    # crawl_tweet_simple()
    crawl_longtext()
