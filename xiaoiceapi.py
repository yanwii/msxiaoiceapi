import requests
import json
import time
import sys
from bs4 import BeautifulSoup
from flask import Flask,request,jsonify
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os

class xiaoiceApi():

    def __init__(self):
        if not os.path.exists("./tmp"):
            os.makedirs("./tmp")
        self.headers = {}
        #self.cookies = self.loadCookies()
        self.loadheaders()

    def loadCookies(self):
        accountInfo = []
        #帐号密码保存在password文件，格式为
        #mail:yourmail
        #password:yourpassword
        with open("./password") as headers:
            line = headers.readline().strip()
            while line:
                accountInfo.append(line.split(":")[1])
                line = headers.readline().strip()
        print(accountInfo)
        firefox = webdriver.Firefox()
        firefox.get('http://weibo.com/')
        time.sleep(15)
        idInputbox = firefox.find_element_by_id('loginname')
        idInputbox.click()
        idInputbox.send_keys(accountInfo[0])
        passInputbox = firefox.find_element_by_class_name('info_list.password')
        passInputbox.click()
        passInputbox.send_keys(accountInfo[1])
        idInputbox.send_keys(Keys.ENTER)
        print("若浏览器未自动关闭请手动输入验证码。。。")
        #这里如果登录太多次需要手动输入验证码
        while True:
            time.sleep(2)
            if 'https://weibo.com/u' in firefox.current_url:
                break
        cookie = [item["name"] + "=" + item["value"] for item in firefox.get_cookies()]
        cookiestr = ';'.join(item for item in cookie)
        firefox.quit()
        return cookiestr

    def loadheaders(self):
        '''
            导入headers
        '''
        with open("./headers.txt") as headers:
            line = headers.readline().strip()
            while line:
                key = line.split(":")[0]
                #firefox里的原始头冒号后面会多出一个空格，需除去
                self.headers[key] = line[len(key)+1:].strip()
                line = headers.readline().strip()

    def dumpheaders(self):
        '''
            保存headers
        '''
        with open("./headers.txt", "w") as headers:
            for key, value in self.headers.items():
                headers.write('{}:{}\n'.format(key, value))


    def chat(self, input_strs):
        '''
        聊天

            args (str):
                input_strs  问题
            return (dict):
                status      状态
                text        内容
        '''
        if not self.headers:
            return self.dicts("error", "请打开浏览器 复制并将headers放入headers.txt中")
        data = {
            'location':'msgdialog',
            'module':'msgissue',
            'style_id':1,
            'text':input_strs,
            'uid':5175429989,
            'tovfids':'',
            'fids':'',
            'el':'[object HTMLDivElement]',
            '_t':0,
        }

        try:
            #原http的api已改为https的api
            url = 'https://weibo.com/aj/message/add?ajwvr=6'
            page = requests.post(url, data=data, headers=self.headers)
            self.savePage(page.text, "./tmp/postpage.txt")
            if page.json()['code'] == '100000':
                code, text, res_type = self.loop(input_strs)
                return self.dicts(code, res_type, text)
            else:
                return self.dicts("500", "failed", page.json()['msg'])
        except Exception as e:
            print("对话失败，重新获取cookies")
            if not os.path.exists("./password"):
                print("请在password中设置好用户名和密码")
                return self.dicts("500", "error", e)
            else:
                self.headers["Cookie"] = self.loadCookies()
                self.dumpheaders()
                return self.dicts("500", "error", e)

    def dicts(self, status, res_type, text):
        '''
            包装return
        '''
        return {"status":status, "type":res_type, "text":text}

    def loop(self, input_strs):
        '''
            刷新直到获取到回答
        '''
        times = 1
        while times <= 20:
            times += 1
            #同上，原http的api已改为https的api,另外headers用全反而无法获取页面，只需用到cookies
            response = requests.get("https://weibo.com/aj/message/getbyid?ajwvr=6&uid=5175429989&count=1&_t=0" , headers={"Cookie":self.headers["Cookie"]})
            self.savePage(response.text, "./tmp/response.txt")
            soup = BeautifulSoup(response.json()['data']['html'], "lxml")
            text = soup.find("p", class_='page')
            if text:
                if text.text == input_strs:
                    time.sleep(0.3)
                    continue
            elif "收起" in soup.get_text():
                #返回imgURL
                imgUrl = soup.find(href=re.compile('msget')).get('href')
                return 200, imgUrl, "img"
                '''
                text = "图片地址： " + imgUrl
                picRespone = requests.get(imgUrl, headers={"Cookie":self.headers["Cookie"]})
                if picRespone.status_code == 200:
                    with open('pic.jpg', 'wb') as f:
                        f.write(picRespone.content)
                img = Image.open('pic.jpg')
                img.show()
                '''

            elif "mp3" in soup.get_text():
                mp3Url = soup.find(href=re.compile('msget')).get('href')
                return 200, mp3Url,"voice"
                # 返回语音URL

                '''
                text = "语音地址： " + imgUrl
                picRespone = requests.get(imgUrl, headers={"Cookie":self.headers["Cookie"]})
                if picRespone.status_code == 200:
                    with open('voice.mp3', 'wb') as f:
                        f.write(picRespone.content)
                '''
            return 200, text.text, "text"
        text = "错误： 已达到最大重试次数"
        return 500, text, "failed"

    def savePage(self, text, file):
        with open(file, "w") as f:
            f.write(text)

    def api(self):
        app = Flask(__name__)

        @app.route("/")
        def index():
            que = request.args.get("que")
            ans = self.chat(que)
            return jsonify(ans)
        app.run()

if __name__ == '__main__':
    xb = xiaoiceApi()
    xb.api()
