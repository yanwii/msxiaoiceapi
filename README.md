# msxiaoiceapi
  
## 说明   
需要  python3+ BeautifulSoup flask 目前暂时只支持文字  

登陆微博 并将headers保存在根目录headers.txt中  
确保已经领养小冰 这里我提供了一个测试账号

## 使用
    py xiaoiceapi.py
    http://127.0.0.1:5000/?que=你是谁
    
    return:
    {  
    "status": "succeed",  
    "text": "你都知道你还问[不屑脸]，哈哈党"  
    }  
