# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/1/17 19:29
# @Author  : cendeavor
# @Site    : 
# @File    : m.py
# @Software: PyCharm

import re
import datetime

def time_fix(time_string):
    """推文时间修复
        将爬虫爬下来的推文时间规范化
    Args:
        time_string: 推文中的时间字符串

    Returns:

    """
    now_time = datetime.datetime.now()

    if '年' in time_string:
        time_string = time_string.replace('年', '-').replace('月', '-').replace('日', ' ')
        return time_string

    if '月' in time_string:
        time_string = time_string.replace('月', '-').replace('日', ' ')
        time_string = str(now_time.year) + '-' + time_string
        return time_string

    if '今天' in time_string:
        return time_string.replace('今天', now_time.strftime('%Y-%m-%d '))

    if '小时前' in time_string:
        minutes = re.search(r'^(\d+)小时', time_string).group(1)
        created_at = now_time - datetime.timedelta(hours=int(minutes))
        return created_at.strftime('%Y-%m-%d %H:%M')

    if '分钟前' in time_string:
        minutes = re.search(r'^(\d+)分钟', time_string).group(1)
        created_at = now_time - datetime.timedelta(minutes=int(minutes))
        return created_at.strftime('%Y-%m-%d %H:%M')

    return time_string
