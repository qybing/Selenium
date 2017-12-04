import json
import random
import re
import time

import pymysql
import requests

from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# driver_path = r'D:\app\QYBing\chromedriver.exe'
# driver_path = r'/usr/bin/phantomjs/phantomjs.exe'
# driver = webdriver.Chrome(executable_path=driver_path)
# driver_path = r'E:\QQ\Mozilla Firefox\geckodriver.exe'
from config import operatorss, first_url, phone, pwd

# driver_path = r'E:\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe'
# export PATH=/root/phantomjs-2.1.1-windows/bin/phantomjs.exe:$PATH


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
    not_result_url = []
    for i in z:
        if int(i[0])<3:
            result_url.append(base_url+i[1])
        else:
            not_result_url.append(base_url+i[1])
    return result_url,not_result_url

def check_urls_to_mysql(urls):
    db = pymysql.connect(host='xxxxxx', user='xxxxxxx', passwd='xxxxxxx', db='xxxxxxxx',
                         charset='utf8')
    cursor = db.cursor()
    sql = "select url from tieba where is_comment!=0"
    is_urls = []
    try:
        cursor.execute(sql)
        rs = cursor.fetchall()
        for row in rs:
            is_urls.append(row[0])
    except Exception as e:
        print(e)
    cursor.close()
    db.close()
    return list(set(urls)-set(is_urls))

def add_comment_direct_urls(urls):
    for url in urls:
        driver = webdriver.PhantomJS()
        driver.get(url)
        driver.delete_all_cookies()
        # 读取登录时存储到本地的cookie
        with open('cookies_tieba{}.json'.format(operatorss), 'r', encoding='utf-8') as f:
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
            print('开始请求目标网址:{}'.format(url))
            driver.get(url)
            print('获取评论')
            driver.maximize_window()
            time.sleep(2)
            driver.find_element_by_xpath('//*[@id="fixed_bar"]/img[2]').click()
            comments = get_add_comment()
            c = random.choice(comments)
            # pattern = re.compile(r'(\d+).{1}')
            # comment = (re.sub(pattern, '', c)).replace(r'\n','').strip()
            print('评论为：{}'.format(c))
            js = "var q=document.documentElement.scrollTop=100000"
            driver.execute_script(js)
            element = WebDriverWait(driver, 10, 1).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ueditor_replace"]/p')))
            element.click()
            element.send_keys(c)
            driver.save_screenshot("zhijie1.png")
            print('正在添加评论')
            send_messages = driver.find_element_by_xpath(
                '//*[@id="tb_rich_poster"]/div[3]/div[3]/div/a/span/em').click()
            try:
                driver.save_screenshot("zhijie2.png")
                check = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, 'dialogJbody')))
                driver.save_screenshot("zhijie3.png")
                save_to_mysql(url, c, 1)
                print("有验证码了，我休息一会")
                time.sleep(3000)
            except Exception as e:
                driver.save_screenshot("zhijie4.png")
                save_to_mysql(url, c, 0)
                print("添加评论成功")
        except Exception as e:
            driver.save_screenshot("zhijie5.png")
            print(e)
            save_to_mysql(url, c, 2)
            print('添加评论失败')
        driver.close()
        te = random.randint(60, 80)
        print('休息{}秒'.format(te))
        time.sleep(te)
    # driver.close()

def add_comment_indirect(urls):
    urls = check_urls_to_mysql(urls[1:])
    # driver = webdriver.PhantomJS()
    for url in urls:
        driver = webdriver.PhantomJS()
        # driver = webdriver.Chrome(executable_path=driver_path)
        driver.get(url)
        driver.delete_all_cookies()
        # 读取登录时存储到本地的cookie
        with open('cookies_tieba{}.json'.format(operatorss), 'r', encoding='utf-8') as f:
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
            print('开始请求目标网址:{}'.format(url))
            driver.get(url)
            driver.set_window_size(400, 300)
            driver.find_element_by_xpath('//*[@id="fixed_bar"]/img[2]').click()
            time.sleep(2)
            # driver.save_screenshot("codingpy9.png")
            send_messages = driver.find_elements_by_xpath(
                '//div[@class="j_lzl_r p_reply"]')
            for i in send_messages[1:]:
                Action = ActionChains(driver)
                Action.move_to_element(i).perform()
                mess = i.get_attribute('data-field')
                pattern = re.compile('"total_num":(.*?)}')
                c = re.search(pattern, mess)
                if c.group(1) == 'null':
                    total_num = 0
                else:
                    total_num = int(c.group(1))
                if total_num < 5:
                    print(mess)
                    print('获取评论')
                    comments = get_add_comment()
                    comment = random.choice(comments)
                    print('评论为：{}'.format(comment))
                    print('正在添加评论.....')
                    if total_num==0 :
                        i.find_element_by_xpath('a').click()
                        time.sleep(2)
                    if total_num>0 and total_num<5:
                        i.find_element_by_xpath('span').click()
                        time.sleep(2)
                        i.find_element_by_xpath('a').click()
                    time.sleep(2)
                    driver.save_screenshot("jianjie1.png")
                    sure = driver.find_element_by_xpath('//span[@class="lzl_panel_submit j_lzl_p_sb"]')
                    Action.move_to_element(sure).perform()
                    driver.save_screenshot("jianjie1.png")
                    element = WebDriverWait(driver, 10, 1).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="j_editor_for_container"]')))
                    time.sleep(4)
                    try:
                        driver.save_screenshot("jianjie2.png")
                        element.send_keys(comment)
                        driver.save_screenshot("jianjie3.png")
                        sure.click()
                        print('有异常请停止')
                    except Exception as e:
                        driver.save_screenshot("jianjie4.png")
                        sure.click()
                        try:
                            driver.save_screenshot("jianjie5.png")
                            check = WebDriverWait(driver, 2).until(
                                EC.presence_of_element_located((By.ID, 'dialogJbody')))
                            save_to_mysql(url, comment, 1)
                            driver.save_screenshot("jianjie6.png")
                            print("有验证码了，我休息一会")
                            time.sleep(3000)
                        except Exception as e:
                            save_to_mysql(url, comment, 0)
                            print("添加评论成功")
                            te = random.randint(60, 100)
                            print('休息{}秒'.format(te))
                            time.sleep(te)
                else:
                    print('本楼回复大于5，跳过')
        except Exception as e:
            print(e)
            save_to_mysql(url, comment, 2)
            print('添加评论失败')

        driver.close()
        te = random.randint(60, 100)
        print('休息{}秒'.format(te))
        time.sleep(te)


def save_to_mysql(url,comment,is_comment):
    db = pymysql.connect(host='xxxxxxx', user='xxxxxx', passwd='xxxxxxx', db='xxxxxxx',
                         charset='utf8')
    cursor = db.cursor()
    sql = "insert into tieba(url,comment,is_comment) values(%s,%s,%s)"
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

def login(phone, pwd,url):
    driver = webdriver.Chrome(executable_path=driver_path)
    driver.get(url)
    driver.find_element_by_xpath('//*[@id="com_userbar"]/ul/li[4]/div/a').click()
    driver.find_element_by_xpath('//*[@id="TANGRAM__PSP_11__userName"]').click()
    driver.find_element_by_xpath('//*[@id="TANGRAM__PSP_11__userName"]').send_keys(phone)
    driver.find_element_by_xpath('//*[@id="TANGRAM__PSP_11__password"]').send_keys(pwd)
    driver.find_element_by_xpath('//*[@id="TANGRAM__PSP_11__submit"]').click()
    dictCookies = driver.get_cookies()
    jsonCookies = json.dumps(dictCookies)
    with open('cookies_tieba4.json', 'w') as f:
        f.write(jsonCookies)
    driver.close()

def get_cookies(url):
    login(phone,pwd,url)

if __name__ == '__main__':
    # get_cookies(first_url[0])
    print('获取目标贴吧...')
    for i in first_url:
        print('获取的帖子...')
        html = get_html(i)
        direct_urls,indirect_urls = get_echo_num(html)
        print('回复小于3的贴的网址：{}'.format(direct_urls))
        print("一共{}个帖子".format(len(direct_urls)))
        add_comment_direct_urls(direct_urls)
        print('获取评论大于5的的帖子...')
        print('回复大于5的贴的网址：{}'.format(indirect_urls))
        print("一共{}个帖子".format(len(indirect_urls)))
        add_comment_indirect(indirect_urls)