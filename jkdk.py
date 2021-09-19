import re
import time
from typing import cast

import requests
from bs4 import BeautifulSoup

# import pytesseract as pt
# import PIL


class Jkdk:
    def __init__(self, uid, upw, key, province, city, position):
        self.src = r'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/login'

        self.key = key
        self.province = province
        self.city = city
        self.position = position
        self.url = 'https://push.xuthus.cc/wx/'

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
            'Referer': self.src
        }

        self.data = {
            'uid': uid, 'upw': upw
        }

        self._uid = uid  # 用户号
        self._upw = upw  # 密码
        self.ptopid = ''
        self.sid = ''
        self.form = {}

    def encode(self, page):
        text = page.text.encode(page.encoding).decode(page.apparent_encoding)
        return text

    def valid(self, page):
        if page.status_code == 200:
            return self.encode(page)
        else:
            return None

    def strSearch(self, res: str, target):
        patterns = re.compile(res)
        outputs = patterns.search(target)
        return outputs

    def parse(self, text, label: str, attrs: dict, target: str):
        bs4 = BeautifulSoup(text, 'lxml')
        body = bs4.find(label, attrs=attrs)
        return body.get(target)

    def push_err(self, err: str):
        try:
            requests.get(self.url+self.key +
                         '/?c='+err)
        except:
            print('微信推送也失败，你只能手动查看是否成功了')
            exit(-1)
        else:
            print('微信推送成功')
            exit(-1)

    # 判断是否已经打过卡
    def ifSigned(self, text) -> bool:
        bs4 = BeautifulSoup(text, 'lxml')
        body = bs4.find('span')
        text = body.string

        # 少考虑了填报不成功的情况
        if text == '今日您还没有填报过' or text == '今日您未成功填报过，请重新上报':
            return False
        else:
            return True

    def jkdk1(self, session):
        try:
            page = session.post(self.src, data=self.data,
                                headers=self.headers)
            text = self.encode(page)  # 得到登陆后的界面，但是还没有开始正式填写
            with open('test2.html', 'w') as f:
                f.write(text)

            output = self.strSearch(r'location="(.*?)"', text)
            self.src = output.group(1)
            outputs = self.strSearch('ptopid=(.*)&sid=(.*)', self.src)

            self.ptopid = outputs.group(1)
            self.sid = outputs.group(2)
        except requests.exceptions.SSLError as e:
            print(str(e))

            if (self.key is None):
                exit(-1)
            else:
                self.push_err('打卡失败，可能是网络问题，可以等待一会')
        except Exception as e:
            print(str(e))

            if (self.key is None):
                exit(-1)
            else:
                self.push_err('打卡失败，应该是你学号密码写错了')

    def jkdk2(self, session):
        page = session.get(self.src, headers=self.headers)
        text = self.encode(page=page)

        with open('test2.html', 'w') as f:
            f.write(text)

        self.src = self.parse(text=text, label='iframe', attrs={
            'id': 'zzj_top_6s'},  target='src')
        outputs = self.strSearch(r'ptopid=(.*)&sid=(.*)', self.src)
        self.ptopid = outputs.group(1)
        self.sid = outputs.group(2)

    def jkdk3(self, session):
        page = session.get(self.src, headers=self.headers)
        text = self.encode(page)

        with open('test3.html', 'w') as f:
            f.write(text)

        # 判断是否已经打过卡
        if self.ifSigned(text) is True:
            print('您已经打过卡了')
            if self.key is not None:
                requests.get(self.url+self.key+'/?c=您已经打过卡了')
                print('微信推送成功')
            exit(0)

        self.src = self.parse(text=text, label='form', attrs={
            'name': 'myform52'}, target='action')

    def get_form2(self, text, label: str, attrs: dict):
        bs4 = BeautifulSoup(text, 'lxml')
        body = bs4.find(label, attrs=attrs)

        data = body.find_all('input')
        for i in data:
            self.form[i.get('name')] = i.get('value')
        self.form['myvs_13'] = 'g'
        self.form["myvs_13a"] = self.province
        self.form["myvs_13b"] = self.city
        self.form["myvs_13c"] = self.position
        self.form['myvs_26'] = '2'

    def jkdk4(self, session):

        form1 = {
            'day6': 'b',
            'did': '1',
            'door': '',
            'men6': 'a',
            'ptopid': self.ptopid,
            'sid': self.sid
        }

        page = session.post(self.src, data=form1, headers=self.headers)
        text = self.encode(page=page)

        with open('test4.html', 'w') as f:
            f.write(text)

        self.get_form2(text=text, label='form', attrs={'name': 'myform52'})
        self.src = self.parse(text=text, label='form', attrs={
            'name': 'myform52'}, target='action')

    def jkdk5(self, session) -> bool:

        page = session.post(self.src, data=self.form,
                            headers=self.headers)  # 填表

        text = self.encode(page)

        with open('test5.html', 'w') as f:
            f.write(text)

        bs4 = BeautifulSoup(text, 'lxml')
        body = bs4.find('form', attrs={'name': 'myform52'})

        text = body.get_text()

        output = re.findall('感谢你今日上报健康状况', text)

        if len(output):
            print('好耶')
            if self.key is not None:
                requests.get(self.url+self.key+'/?c=打卡成功')
                print('微信推送成功')
            return True
        else:
            print('不好')
            if self.key is not None:
                requests.get(self.url+self.key+'/?c=打卡失败')
            return False

    def jkdk(self):
        session = requests.Session()
        self.jkdk1(session)
        self.jkdk2(session=session)
        self.jkdk3(session)
        self.jkdk4(session=session)
        result = self.jkdk5(session=session)
