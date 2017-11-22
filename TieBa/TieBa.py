import json
import re
import time
from random import choice

import requests

from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tieba.config import phone, pwd, first_url

driver_path = r'D:\app\QYBing\chromedriver.exe'
# driver_path = r'E:\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe'
# driver = webdriver.Chrome(executable_path=driver_path)

# driver_path = r'E:\QQ\Mozilla Firefox\geckodriver.exe'
# driver = webdriver.Firefox(executable_path=driver_path)

def get_html(url):
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Host': 'tieba.baidu.com',
    }
    for tries in range(5):
        try:
            content = requests.get(url, headers=headers, timeout=30).text
            return content
        except:
            if tries < (5 - 1):
                time.sleep(tries + 1)  # have a rest
                print('retry:' + url)
                continue
            else:
                print('did not get data')
                return ''


def get_echo_num(html):
    numss = '<span class="threadlist_rep_num center_text".*?title="回复">(\d+)</span>'
    result = re.findall(numss,html,re.S)
    url_=".*?field='{&quot;id&quot;:(\d+)"
    result1 = re.findall(url_,html,re.S)
    base_url='https://tieba.baidu.com/p/'
    z = zip(result,result1)
    result_url = []
    for i in z:
        if int(i[0])<3:
            # print(i)
            result_url.append(base_url+i[1])
    return result_url
    # print(result_url)


def add_comment(url):
    driver = webdriver.Chrome(executable_path=driver_path)
    driver.get(url)
    driver.delete_all_cookies()
    # 读取登录时存储到本地的cookie
    with open('cookies.json', 'r', encoding='utf-8') as f:
        listCookies = json.loads(f.read())
    for cookie in listCookies:
        driver.add_cookie({
            'domain': '.tieba.baidu.com',  # 此处xxx.com前，需要带点
            'name': cookie['name'],
            'value': cookie['value'],
            'path': '/',
            'secure': False,
            'httpOnly': cookie['httpOnly']
        })
    try:
        driver.get(url)
        comments = get_add_comment()
        c = choice(comments)
        pattern = re.compile(r'(\d+).{1}')
        comment = re.sub(pattern, '', c)
        js = "var q=document.documentElement.scrollTop=100000"
        driver.execute_script(js)
        element = WebDriverWait(driver, 10,1).until(
            EC.presence_of_element_located((By.ID,'ueditor_replace')))
        # element.click()
        # element.click()
        element.send_keys(comment.replace(r'\n',''))
        send_messages = driver.find_element_by_xpath(
            '//*[@id="tb_rich_poster"]/div[3]/div[3]/div/a/span/em').click()
        try:
            check = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, 'dialogJbody')))
            time.sleep(80)
        except Exception as e:
            print("添加评论成功")
    except Exception as e:
        print(e)
        print('添加评论失败')
    driver.close()
        # continue
def get_add_comment():
    comments = []
    with open('comment', 'r', encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            comments.append(line.replace(r'\n', ''))
    return comments

def login(phone, pwd):
    driver = webdriver.Chrome(executable_path=driver_path)
    driver.get('https://tieba.baidu.com/f?kw=cos%E9%9B%B6%E7%94%A8%E9%92%B1&ie=utf-8')
    driver.find_element_by_xpath('//*[@id="com_userbar"]/ul/li[4]/div/a').click()
    driver.find_element_by_xpath('//*[@id="TANGRAM__PSP_11__userName"]').click()
    driver.find_element_by_xpath('//*[@id="TANGRAM__PSP_11__userName"]').send_keys(phone)
    driver.find_element_by_xpath('//*[@id="TANGRAM__PSP_11__password"]').send_keys(pwd)
    driver.find_element_by_xpath('//*[@id="TANGRAM__PSP_11__submit"]').click()
    dictCookies = driver.get_cookies()
    jsonCookies = json.dumps(dictCookies)
    with open('cookies.json', 'w') as f:
        f.write(jsonCookies)

def get_cookies():
    login(phone, pwd)

if __name__ == '__main__':
    # get_cookies()
    html = get_html(first_url[0])
    urls = get_echo_num(html)
    print(urls)
    for url in urls:
        add_comment(url)
        time.sleep(5)