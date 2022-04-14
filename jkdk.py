import re

import requests
from bs4 import BeautifulSoup

# import pytesseract as pt
# import PIL


class Jkdk:
    def __init__(self, uid, upw, key, province, city, position):
        self.src = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/login'
        self.src2 = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb?ptopid={ptosid}&sid={sid}&fun2='

        self.key = key
        self.province = province
        self.city = city
        self.position = position
        self.url = 'https://service-rnuqqxkb-1300650038.sh.apigw.tencentcs.com/release/getuid'

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:98.0) Gecko/20100101 Firefox/98.0',
            "Accept-Language": "en-SG,en-GB;q=0.9,en;q=0.8",
            "Content-Type": 'application/x-www-form-urlencoded',
            'Accept-Encoding': 'gzip, deflate, br',
        }

        self.data = {
            'uid': uid, 'upw': upw
        }

        self._uid = uid  # 用户号
        self._upw = upw  # 密码
        self.ptopid = ''
        self.sid = ''
        self.form2 = {}
        self.form1 = {}
        self.fun18 = ''

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
            requests.post(self.url, json={'uid': self.key, 'content': err})
        except:
            print('微信推送也失败，你只能手动查看是否成功了')
            return False
        else:
            print('微信推送成功')
            return False

    # 判断是否已经打过卡
    def ifSigned(self, body) -> bool:
        sign = body.find('span')
        text = sign.contents[0]
        # 少考虑了填报不成功的情况
        if text == '今日您还没有填报过' or text == '今日您未成功填报过，请重新上报':
            return False
        else:
            return True

    def jkdk1(self, session):
        try:
            data = self.data
            data['hh28'] = '729'
            data['smbtn'] = '进入健康状况上报平台'
            page = session.post(self.src, data=data,
                                headers=self.headers)

            text = self.encode(page)  # 得到登陆后的界面，但是还没有开始正式填写
            with open('test.html', 'w') as f:
                f.write(text)

            output = self.strSearch(r'location="(.*?)"', text)
            self.src = output.group(1)
            outputs = self.strSearch('ptopid=(.*)&sid=(.*)', self.src)
            self.ptopid = outputs.group(1)
            self.sid = outputs.group(2)
            print(self.ptopid, self.sid, self.src)
        except requests.exceptions.SSLError as e:
            print(str(e))

            if (self.key is None):
                return False
            else:
                self.push_err('打卡失败，可能是网络问题，可以等待一会')
        except Exception as e:
            print(str(e))

            if (self.key is None):
                return False
            else:
                self.push_err('打卡失败，应该是你学号密码写错了')
        return True

    # get fun18 value
    def jkdk2(self, session) -> bool:
        headers = self.headers
        headers['Referer'] = self.src
        page = session.get(self.src2.format(ptosid=self.ptopid, sid=self.sid))
        text = self.encode(page)
        bs4 = BeautifulSoup(text, 'lxml')
        body = bs4.find('form', attrs={'name': "myform52"})
        hidden = body.find_all(name='input', attrs={'type': 'hidden'})
        fun18 = hidden[2].get('value')
        self.fun18 = fun18
        print(f'fun18={fun18}')

        # 判断是否已经打过卡
        if self.ifSigned(body) is True:
            print('您已经打过卡了')
            if self.key is not None:
                requests.post(self.url, json={
                              'uid': self.key, 'content': '您已经打过卡了'})
                print('微信推送成功')
            return False
        return True

    def get_form1(self, data):
        data = self.data
        data['did'] = '1'
        data['door'] = ''
        data['men6'] = 'a'
        data['ptopid'] = self.ptopid
        data['sid'] = self.sid
        data['fun18'] = self.fun18
        self.form1 = data

    def jkdk3(self, session):
        self.get_form1(self.data)

        page = session.post(self.src, headers=self.headers, data=self.form1)
        text = self.encode(page=page)

        with open('test3.html', 'w') as f:
            f.write(text)

        self.src = self.parse(text=text, label='iframe', attrs={
            'id': 'zzj_fun_426s'},  target='src')
        outputs = self.strSearch(r'ptopid=(.*)&sid=(.*)', self.src)
        self.ptopid = outputs.group(1)
        self.sid = outputs.group(2)

    def jkdk4(self, session):

        form = {
            'did': '1',
            'men6': 'a',
            'fun18': self.fun18,
            'ptopid': self.ptopid,
            'sid': self.sid,
        }
        self.src = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb'

        page = session.post(self.src, headers=self.headers, data=form)
        text = self.encode(page)

        with open('test4.html', 'w') as f:
            f.write(text)

        self.get_form2(
            text=text, label='form', attrs={'name': 'myform52'})

    def get_form2(self, text, label: str, attrs: dict):
        bs4 = BeautifulSoup(text, 'lxml')
        body = bs4.find(label, attrs=attrs)

        data = body.find_all('input')
        for i in data:
            self.form2[i.get('name')] = i.get('value')
        self.form2["myvs_13a"] = self.province
        self.form2["myvs_13b"] = self.city
        self.form2["myvs_13c"] = self.position
        self.form2['myvs_26'] = '2'
        self.form2['did'] = '2'
        self.form2['men6'] = 'a'
        self.form2['fun18'] = self.fun18
        self.form2['ptopid'] = self.ptopid
        self.form2['sid'] = self.sid
        self.form2['sheng6'] = ''
        self.form2['shi6'] = ''
        self.form2['jingdu'] = '113.631419'
        self.form2['weidu'] = '34.753439'

    def jkdk5(self, session) -> bool:

        page = session.post(self.src, data=self.form2,
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
                requests.post(self.url, json={
                              'uid': self.key, 'content': '打卡成功'})
                print('微信推送成功')
            return True
        else:
            print('不好')
            if self.key is not None:
                requests.post(self.url, json={
                              'uid': self.key, 'content': '打卡失败'})
            return False

    def jkdk(self):
        session = requests.Session()
        res = self.jkdk1(session)
        if res:
            if self.jkdk2(session=session):
                self.jkdk3(session)
                self.jkdk4(session=session)
                res = self.jkdk5(session=session)
