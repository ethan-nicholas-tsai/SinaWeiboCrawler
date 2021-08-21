import sys
from datetime import datetime, timedelta, date
from weibo.utils.region import region_dict
from weibo.middlewares import *
from weibo.settings import DEFAULT_REQUEST_HEADERS


def get_headers_and_proxies():
    headers = DEFAULT_REQUEST_HEADERS
    headers['User-Agent'] = UAMiddleware.get_ua()
    proxy = ProxyMiddleware.get_proxy()
    proxies = {
        'http': proxy,
        'https': proxy
    }
    return headers, proxies


def convert_weibo_type(weibo_type):
    """将微博类型转换成字符串"""
    if weibo_type == 0:
        return '&typeall=1'
    elif weibo_type == 1:
        return '&scope=ori'
    elif weibo_type == 2:
        return '&xsort=hot'
    elif weibo_type == 3:
        return '&atten=1'
    elif weibo_type == 4:
        return '&vip=1'
    elif weibo_type == 5:
        return '&category=4'
    elif weibo_type == 6:
        return '&viewpoint=1'
    return '&scope=ori'


def convert_contain_type(contain_type):
    """将包含类型转换成字符串"""
    if contain_type == 0:
        return '&suball=1'
    elif contain_type == 1:
        return '&haspic=1'
    elif contain_type == 2:
        return '&hasvideo=1'
    elif contain_type == 3:
        return '&hasmusic=1'
    elif contain_type == 4:
        return '&haslink=1'
    return '&suball=1'


def get_keyword_list(file_name):
    """获取文件中的关键词列表"""
    with open(file_name, 'rb') as f:
        try:
            lines = f.read().splitlines()
            lines = [line.decode('utf-8-sig') for line in lines]
        except UnicodeDecodeError:
            print(u'%s文件应为utf-8编码，请先将文件编码转为utf-8再运行程序', file_name)
            sys.exit()
        keyword_list = []
        for line in lines:
            if line:
                keyword_list.append(line)
    return keyword_list


def get_regions(region):
    """根据区域筛选条件返回符合要求的region"""
    new_region = {}
    if region:
        for key in region:
            if region_dict.get(key):
                new_region[key] = region_dict[key]
    if not new_region:
        new_region = region_dict
    return new_region


def standardize_date(created_at):
    """标准化微博发布时间"""
    if "刚刚" in created_at:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    elif "秒" in created_at:
        second = created_at[:created_at.find(u"秒")]
        second = timedelta(seconds=int(second))
        created_at = (datetime.now() - second).strftime("%Y-%m-%d %H:%M")
    elif "分钟" in created_at:
        minute = created_at[:created_at.find(u"分钟")]
        minute = timedelta(minutes=int(minute))
        created_at = (datetime.now() - minute).strftime("%Y-%m-%d %H:%M")
    elif "小时" in created_at:
        hour = created_at[:created_at.find(u"小时")]
        hour = timedelta(hours=int(hour))
        created_at = (datetime.now() - hour).strftime("%Y-%m-%d %H:%M")
    elif "今天" in created_at:
        today = datetime.now().strftime('%Y-%m-%d')
        created_at = today + ' ' + created_at[2:]
    elif '年' not in created_at:
        year = datetime.now().strftime("%Y")
        month = created_at[:2]
        day = created_at[3:5]
        time = created_at[6:]
        created_at = year + '-' + month + '-' + day + ' ' + time
    else:
        year = created_at[:4]
        month = created_at[5:7]
        day = created_at[8:10]
        time = created_at[11:]
        created_at = year + '-' + month + '-' + day + ' ' + time
    return created_at


def str_to_time(text):
    """将字符串转换成时间类型"""
    result = datetime.strptime(text, '%Y-%m-%d')
    return result


def iter_date(start_date, end_date, day_gap=1, reverse=False):
    """ 生成开始日期到结束日期间的所有日期

    Args:
        start_date: 开始日期，'yyyy-mm-dd'字符串
        end_date: 结束日期，'yyyy-mm-dd'字符串
        day_gap: 生成的相隔多少天
        reverse: 逆序生成日期

    Returns:
        string类型日期的生成器
    """
    start_time = tuple([int(_) for _ in start_date.split('-')])
    end_time = tuple([int(_) for _ in end_date.split('-')])
    begin = date(*start_time)
    end = date(*end_time)  # 使用元组拆包的方法
    d = begin if not reverse else end
    delta = timedelta(days=day_gap)
    if not reverse:
        while d <= end:
            # print(d.strftime("%Y-%m-%d"))
            yield d.strftime("%Y-%m-%d")
            d += delta
    else:
        while d >= begin:
            # print(d.strftime("%Y-%m-%d"))
            yield d.strftime("%Y-%m-%d")
            d -= delta


# -----------------colorama模块的一些常量---------------------------
# Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Style: DIM, NORMAL, BRIGHT, RESET_ALL
#

from colorama import init, Fore, Back, Style

init(autoreset=True)


class Colored(object):

    #  前景色:红色  背景色:默认
    @staticmethod
    def red(s):
        return Fore.RED + s + Fore.RESET

    #  前景色:绿色  背景色:默认
    @staticmethod
    def green(s):
        return Fore.GREEN + s + Fore.RESET

    #  前景色:黄色  背景色:默认
    @staticmethod
    def yellow(s):
        return Fore.YELLOW + s + Fore.RESET

    #  前景色:蓝色  背景色:默认
    @staticmethod
    def blue(s):
        return Fore.BLUE + s + Fore.RESET

    #  前景色:洋红色  背景色:默认
    @staticmethod
    def magenta(s):
        return Fore.MAGENTA + s + Fore.RESET

    #  前景色:青色  背景色:默认
    @staticmethod
    def cyan(s):
        return Fore.CYAN + s + Fore.RESET

    #  前景色:白色  背景色:默认
    @staticmethod
    def white(s):
        return Fore.WHITE + s + Fore.RESET

    #  前景色:黑色  背景色:默认
    @staticmethod
    def black(s):
        return Fore.BLACK

    #  前景色:白色  背景色:绿色
    @staticmethod
    def white_green(s):
        return Fore.WHITE + Back.GREEN + s + Fore.RESET + Back.RESET

    ################## @@@@@@@@@@@@@@  #######################

    @staticmethod
    def yellow_light_green(s):
        return Fore.YELLOW + Back.LIGHTGREEN_EX + s + Fore.RESET + Back.RESET

    @staticmethod
    def black_light_magenta(s):
        return Fore.BLACK + Back.LIGHTMAGENTA_EX + s + Fore.RESET + Back.RESET

    #################### Bad Attempt ########################
    @staticmethod
    def red_cyan(s):
        return Fore.RED + Back.CYAN + s + Fore.RESET + Back.RESET

    @staticmethod
    def red_yellow(s):
        return Fore.RED + Back.YELLOW + s + Fore.RESET + Back.RESET

    @staticmethod
    def red_blue(s):
        return Fore.RED + Back.BLUE + s + Fore.RESET + Back.RESET

    @staticmethod
    def yellow_blue(s):
        return Fore.YELLOW + Back.BLUE + s + Fore.RESET + Back.RESET

    @staticmethod
    def yellow_cyan(s):
        return Fore.YELLOW + Back.CYAN + s + Fore.RESET + Back.RESET

    @staticmethod
    def yellow_light_magenta(s):
        return Fore.YELLOW + Back.LIGHTMAGENTA_EX + s + Fore.RESET + Back.RESET

# print(Colored.red('I am red!'))
# print(Colored.green('I am gree!'))
# print(Colored.yellow('I am yellow!'))
# print(Colored.blue('I am blue!'))
# print(Colored.magenta('I am magenta!'))
# print(Colored.cyan('I am cyan!'))
# print(Colored.white('I am white!'))
# print(Colored.white_green('I am white green!'))
