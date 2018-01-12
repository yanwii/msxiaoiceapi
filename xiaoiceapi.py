import requests
import json
import time
import sys
from bs4 import BeautifulSoup
from flask import Flask,request,jsonify
import re
from PIL import Image

class xiaoiceApi():
    
    def __init__(self):
        self.headers = {}
        self.loadheaders()

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
                text = self.loop(input_strs)
                return self.dicts("succeed", text)
            else:
                return self.dicts("failed", page.json()['msg'])
        except Exception as e:
            return self.dicts("error", e)
    
    def dicts(self, status, text):
        '''
            包装return
        '''
        return {"status":status, "text":text}

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
                text = text.text
                if text == input_strs:
                    continue
            elif "收起" in soup.get_text():
                imgUrl = soup.find(href=re.compile('msget')).get('href')
                text = "图片地址： " + imgUrl
                picRespone = requests.get(imgUrl, headers={"Cookie":self.headers["Cookie"]})
                if picRespone.status_code == 200:
                    with open('pic.jpg', 'wb') as f:
                        f.write(picRespone.content)
                img = Image.open('pic.jpg')
                img.show()
            elif "mp3" in soup.get_text():
                mp3Url = soup.find(href=re.compile('msget')).get('href')
                text = "语音地址： " + imgUrl
                picRespone = requests.get(imgUrl, headers={"Cookie":self.headers["Cookie"]})
                if picRespone.status_code == 200:
                    with open('voice.mp3', 'wb') as f:
                        f.write(picRespone.content)
            else:
                print("第{}次重试".format(times))
                continue
            time.sleep(0.3)
            return text
        text = "错误： 已达到最大重试次数"
        print (text)
        return text
            
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
