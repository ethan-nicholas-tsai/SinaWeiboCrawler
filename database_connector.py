#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/11/17 13:08
# @Author  : cendeavor
# @File    : database.py
# @Software: PyCharm


import pymongo


class MongoDBC:
    """MongoDBConnector

    """

    def __init__(self, uri, dbname, username, password):
        # 重写该类或者填充本地数据库配置信息
        self.uri = uri
        self.database = dbname
        self.username = username
        self.password = password

    def connect(self):
        client = pymongo.MongoClient(self.uri)
        database = client[self.database]
        database.authenticate(self.username, self.password)
        self.db = database
        self.cli = client
        return self.db

    def close(self):
        self.cli.close()
