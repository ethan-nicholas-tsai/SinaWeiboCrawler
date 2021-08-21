#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 9:31
# @Author  : cendeavor
# @Site    : 
# @File    : database_manager.py
# @Software: PyCharm

from database_connector import MongoDBC
from pprint import pprint


class MongoDBM(MongoDBC):
    """MongoDBManager
    设计理念：
    1. 给一定一套连接参数并new一个Manager，可以得到一个db操作对象；
    2. 类的help函数里面提供了类依赖库的使用demo；
    3. 类本身提供一套“基础”db操作集（参数db无关），可以用于辅助开发者操作数据库；
    4. 也提供一套实用操作集（参数中含db，但任务无关），这是开发的时候总结出来可能会重复用到的操作，开发者也可以自己去写但没必要
    """

    def __init__(self, uri, dbname, username, password):
        super(MongoDBM, self).__init__(uri=uri, dbname=dbname,
                                       username=username,
                                       password=password)

    @staticmethod
    def stats_collection(db, cname, key=None):
        """集合统计函数
            返回集合的一些基本统计数据，比如count之类
        Args:
            db: 建立连接后的数据库可操作对象
            cname: 目标集合名
            key: 用于筛选的键值名（考虑后面改成condition字典形式）

        Returns:
            stats: 关于集合的一些统计数据

        """
        stats = {
            'total': db[cname].count(),
            'unique': {},
        }
        if key:
            stats['unique'][key] = len(db[cname].distinct(key))
        print(stats)
        return stats

    @staticmethod
    def remove_empty_record(db, cname, key, info=True):
        """去空记录

        Args:
            db: 建立连接后的数据库可操作对象
            cname: 目标集合名
            key: 指定必须不为空的字段
            info: 是否打印输出到终端

        Returns:

        """
        if info:
            res = {}
            stats = MongoDBM.stats_collection(db, cname, key=key)
            res['pre_total_num'] = stats['total']

        collection = db[cname]
        collection.remove({key: None})

        if info:
            print('[ Remove Empty Records ]')
            stats = MongoDBM.stats_collection(db, cname, key=key)
            res['cur_total_num'] = stats['total']
            res['removed_empty_records'] = res['cur_total_num'] - res['pre_total_num']
            pprint(res)

    @staticmethod
    def remove_duplicate_record(db, cname, key, info=True):
        """数据库去重
            根据 key 删除数据库中重复的记录
        Args:
            db: 建立连接后的数据库可操作对象
            cname: 目标集合名
            key: 指定必须唯一的字段
            info: 是否打印输出到终端

        Returns:

        """
        if info:
            stats = MongoDBM.stats_collection(db, cname, key=key)
            total_num = stats['total']
            distinct_num = stats['unique'][key]
            print("[ Before Deletion ]")
            print("Repeat Rate: %.2f, Total Num: %d, Distinct Num: %d" % (
                100 * (total_num - distinct_num) / total_num, total_num, distinct_num))
            if total_num == distinct_num:
                return

        collection = db[cname]
        for idx, val in enumerate(collection.distinct(key)):  # 使用distinct方法，获取每一个独特的元素列表
            if not idx % 1000:
                print("*" * 5 + " " + str(idx) + " " + "*" * 5)
            num = collection.count({key: val})  # 统计每一个元素的数量
            for i in range(1, num):  # 根据每一个元素的数量进行删除操作，当前元素只有一个就不再删除
                print('delete %s %d times ' % (val, i))
                # 注意后面的参数， 很奇怪，在mongo命令行下，它为1时，是删除一个元素，这里却是为0时删除一个
                collection.remove({key: val}, 0)

        if info:
            stats = MongoDBM.stats_collection(db, cname, key=key)
            total_num = stats['total']
            distinct_num = stats['unique'][key]
            print("[ After Deletion ]")
            print("Repeat Rate: %.2f, Total Num: %d, Distinct Num: %d" % (
                100 * (total_num - distinct_num) / total_num, total_num, distinct_num))

    @staticmethod
    def backup(db, cname):
        with db[cname].find({}, no_cursor_timeout=True) as cursor:
            cnt = 0
            for item in cursor:
                db[cname + '_copy'].insert(item)
                cnt += 1
                if not cnt % 1000:
                    print(cnt, end=" ", flush=True)
                if not cnt % 10000:
                    print()
        print('done')
