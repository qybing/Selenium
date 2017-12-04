import json
import random
import re
import time

import pymysql
import requests
from fake_useragent import UserAgent
from parsel import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# driver_path = r'D:\app\QYBing\chromedriver.exe'
# driver_path = r'E:\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe'
# driver = webdriver.Chrome(executable_path=driver_path)
# driver_path = r'E:\QQ\Mozilla Firefox\geckodriver.exe'
# driver = webdriver.Firefox(executable_path=driver_path)
def get_html(url):
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Referer': 'https://www.douban.com/group/',
        'Host': 'www.douban.com',
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
    tree = Selector(text=html)
    num = tree.xpath('//*[@id="group-topics"]/div[2]/table/tr')
    urls = []
    for i in num[1:]:
        topic = i.xpath('td[1]/a/text()').extract()
        url = i.xpath('td[1]/a/@href').extract()
        author = i.xpath('td[2]/text()').extract()
        nums = i.xpath('td[3]/text()').extract()
        # print(nums)
        if nums:
            if int(nums[0]) < 3:
                urls.extend(url)
                # print('标题：{}    话题网址：{}    次数：{}'.format(topic,url, nums[0]))
                # add_comment(url)
        else:
            urls.extend(url)
            # print('标题：{}    话题网址：{}    次数：{}'.format(topic, url,0))
    return urls
    # return urls
    #
    # return urls


def add_comment(urls):
    for url in urls:
        driver = webdriver.PhantomJS()
        driver.get(url)
        driver.delete_all_cookies()
        # 读取登录时存储到本地的cookie
        with open('cookies_douban.json', 'r', encoding='utf-8') as f:
            listCookies = json.loads(f.read())
        for cookie in listCookies:
            driver.add_cookie({
                'domain': '.douban.com',  # 此处xxx.com前，需要带点
                'name': cookie['name'],
                'value': cookie['value'],
                'path': '/',
                'secure': False,
                'httpOnly': cookie['httpOnly']
            })
        try:
            print('开始请求目标网址:{}'.format(url))
            driver.get(url)
            print('获取评论')
            comments = get_add_comment()
            c = random.choice(comments)
            # pattern = re.compile(r'(\d+).{1}')
            # comment = (re.sub(pattern, '', c)).replace(r'\n', '').strip()
            print('评论为：{}'.format(c))
            js = "var q=document.documentElement.scrollTop=100000"
            driver.execute_script(js)
            # driver.find_element_by_xpath('//*[@id="last"]').click()
            print('正在添加评论')
            driver.find_element_by_xpath('//*[@id="last"]').send_keys(c)
            send_messages = driver.find_element_by_xpath('//*[@id="content"]/div/div[1]/div[3]/form/span[1]/input').click()
            try:
                check = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, 'captcha_image')))
                save_to_mysql(url, c, 1)
                print("有验证码了，我休息一会")
                time.sleep(500)
            except Exception as e:
                print("添加评论成功")
                save_to_mysql(url, c,0)
        except Exception as e:
            print(e)
            save_to_mysql(url, c, 2)
            print('添加评论失败')
        driver.close()
        te = random.randint(60, 100)
        print('我要休息{}秒再来发帖'.format(te))
        time.sleep(te)

def save_to_mysql(url,comment,is_comment):
    db = pymysql.connect(host='xxxx', user='xxxx', passwd='xxxxx', db='xxxxxx',
                         charset='utf8')
    cursor = db.cursor()
    sql = "insert into douban(url,comment,is_comment) values(%s,%s,%s)"
    try:
        cursor.execute(sql,(url,comment,is_comment))
        db.commit()
    except Exception as e:
        print(e)
    cursor.close()
    db.close()

def get_add_comment():
    comments = []
    with open('comment', 'r', encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            comments.append(line.replace(r'\n', ''))
    return comments

if __name__ == '__main__':
    while True:
        url_=['https://www.douban.com/group/582663/','https://www.douban.com/group/521120/','https://www.douban.com/group/399184/','https://www.douban.com/group/544764/','https://www.douban.com/group/515085/']
        print('获取评论少于3的帖子...')
        for i in url_:
            html = get_html(i)
            urls = get_echo_num(html)
            print('一共是{}个帖子：'.format(len(urls)))
            add_comment(urls)
            print('休息5分钟')
            time.sleep(300)
