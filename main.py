import typing
import requests
import logging
import hashlib
import json
import time
import random
import datetime
import argparse


# 学车不APP登录密码
password = 'xxxx'
username = 'xxxx'

logging.basicConfig(level=logging.DEBUG)
logger =  logging.getLogger('spider1')

def send_msg(rq: typing.Dict):
    """
        发送信息给你自己，提醒你有号了。需要自己实现，可以是邮件、微信。。尽可能拓展
        Args:
            rq: 学车不API返回的信息, 例子：
            {'IsBpked': False, 'IsBpked_SK': 0, 
            'IsCreate': False, 'IsShowSL': '0', 'KS': 0, 
            'QsName': None, 'Qsid': None, 'SL': 0, 'Xnsd': '812', 
            'XnsdName': None, 'YyClInfo': '', 'Yyrq': '2021/03/07 16:08:57', 
            'YyrqXH': 0}
        Returns:
            空

    """
    print(json.dumps(rq))


def try_login(s: requests.Session) -> requests.Session:
        """
            Args:
                s: requests.Session对象，可以使用init_s()伪装过的Session对象

            Returns:
                (s, xxzh)
                zzxh下单使用代码和已经登陆过的Session对象

            Raises:
                Exception: 登录返回码校验失败
                
        """
# 登录学车不，获取WebUI Token
        d = s.post(
            'http://api.xuechebu.com/usercenter/userinfo/login',
            data={
                'username':username,
                'passwordmd5': hashlib.md5(password.encode()).hexdigest()
            }
        )
        r1 = d.json()
        msg1 = r1['message']
        if r1['code'] == 0:
            data1 = r1['data']
            # 登录龙泉驾校使用
            jgid = data1['JGID']
            xybh = data1['XYBH']

            # 登录驾校
            d2 = s.get(
                'http://longquanapi.xuechebu.com/Student/setbadingstuinfo',
                params={
                    'password': password,
                    'jgid': jgid,
                    'xybh': xybh
                }
            )
            r2 = d2.json()
            msg2 = r2['message']
            
            if r2['code'] == 0:
                xxzh = r2['data']['Xxzh']
                return (s, xxzh)
            else:
                logger.error(f'登录驾校失败，检查！{msg2}')
                raise Exception

        else:
            logger.error(f'登录学车不失败，检查！{msg1}')
            raise Exception

def init_s() -> requests.Session:
    """
    Returns:
        已经伪装过的Session对象
    """
    s = requests.Session()
    # s.proxies = {"http": "http://172.17.128.1:8866"}
    s.headers = {"User-Agent": 'android_xuechebu;v7.1.0;phone:SM-G9650:10;'}
    s.mount('http://', requests.adapters.HTTPAdapter(max_retries=5))
    return s

def get_cnbh(s, xxzh):
    """
    Args:
        s: requests.Session对象，try_login()后的Session对象
        xxzh: 未知，从学员信息中提取
    Returns:
        CNBH
    Raises:
        KeyError: 获取CNBH失败
    """
    r = s.get(
        'http://longquanapi.xuechebu.com/Student/StudyInfo',
        params={
            'xxzh': xxzh
        }
    )
    d = r.json()
    return d['data']['CNBH']


def try_order(s, cnbh, xxzh, xnsd, riqi_str):
    """
    Args:
        s: requests.Session对象，try_login()后的Session对象
        cnbh: 教练ID, 每个人只针对一个ID
        xxzh: 未知，从学员信息中提取
        xnsd: 未知，从学员信息中提取
        riqi_str: 预约日期，格式例子：2021-03-02
    Returns:
        状态码，数字类型
    """
    r = s.get(
        'http://longquanapi.xuechebu.com/KM2/ClYyAddByMutil',
        params={
            'params': f"{cnbh}.{riqi_str}.{xnsd}.",
            'isJcsdYyMode': "1",
            'ossdk': '29',
            'os': 'an',
            'appversion': '7.1.0',
            'osversion': '10',
            'version': '7.1.0',
            'cnbh': cnbh,
            'xxzh': xxzh,
        }
    )
    data = r.json()
    if data['code'] == 0:
        logger.info("自动下单成功！！")
    else:
        logger.info(f"自动下单返回消息 {data['message']}")
    return data['code']

def main():
    s = init_s()
    s, xxzh = try_login(s)
    # 列表查询使用
    while True:
        try:
            d3 = s.get(
                'http://longquanapi.xuechebu.com/KM2/ClYyTimeSectionUIQuery2',
                params={
                    'ossdk': '29',
                    'os': 'an',
                    'trainType': '',
                    'xxzh': xxzh,
                    'appversion': '7.1.0',
                    'osversion': '10',
                    'version': '7.1.0'
                }
            )
            logger.info('查询。。。')
            cnbh = get_cnbh(s, xxzh=xxzh)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            logger.info('连接超时。。。等待重试')
            time.sleep(10)
            continue
        except KeyError:
            logger.info('获取CNBH失败。。。等待重试')
            time.sleep(20)
            continue
        
        r3 = d3.json()
        msg3 = r3['message']
        if r3['code'] == 0:
            data3 = r3['data']
            yyrq_list = data3['YyrqList']
            for rq in data3['UIDatas']:
                # TODO(1) 学车不APP显示的预约不可用信息也是从JSON中取到的，找到他，并添加判断
                if rq['SL'] > 0:
                    logger.info('有号了！！！')
                    send_msg(rq)
                    riqi = datetime.datetime.strptime(rq['Yyrq'],"%Y/%m/%d %H:%M:%S")
                    for i in yyrq_list:
                        if i['Yyrq'] == rq['Yyrq']:
                            if i['DisplayWeek'] == '周六' or i['DisplayWeek'] == '周日':
                                continue

                    xnsd = rq['Xnsd']

                    # XNSD: 812 8点到12点，15 13点到17点，夜间不考虑
                    if xnsd == '812' or xnsd == '15':
                        code = None
                        # 重试连续三次下单
                        for i in range(3):
                            if i > 0:
                                s.close()
                                s = init_s()
                                s, xxzh = try_login(s)
                            code = try_order(s, cnbh ,xxzh, xnsd, riqi_str=datetime.datetime.strftime(riqi, "%Y-%m-%d"))
                            if code == 0:
                                break
                        # if code is None or code > 0:
                        
            time.sleep(random.randrange(60, 120))
        else:
            logger.error(f'查询列表失败，检查！{msg3}')
            s.close()
            s = init_s()
            s, xxzh = try_login(s)
            continue



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='自动学车不查询下单查询应用')
    parser.add_argument('-u', action='store', dest="username",type=str,
                        help='用户名', required=True)
    parser.add_argument('-p', action='store', dest="password",type=str,
                        help='密码', required=True)

    args = parser.parse_args()

    password = args.password
    username = args.username
    
    main()
