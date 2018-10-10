from selenium import webdriver
import time
import pickle
import sqlite3
import re
from bs4 import BeautifulSoup
import logging
import sys, os


# 路径调整为代码路径
dirname = os.path.dirname(os.path.abspath(__file__))
sys.path.append(dirname)
os.chdir(dirname)

LOGINNAME = ''
PASSWORD = ''

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s') 

class weibo_scraping:
    def __init__(self):
        self.driver = webdriver.Chrome() # 打开chrome驱动
        self.driver.maximize_window()
        self.driver.get('http://weibo.com')
        while 1:
            try:
                self.driver.implicitly_wait(10)
                break
            except:
                self.driver.refresh()
        self.init_datebase()

    def init_datebase(self):
        '''初始化数据库'''
        self.__conn = sqlite3.connect('weibo.db')
        self.__c = self.__conn.cursor()
        try:
            self.__c.execute("CREATE TABLE IF NOT EXISTS all_users (username TEXT, detail TEXT, text_in_japan TEXT, page_link TEXT, first_page_texts TEXT)")
        except sqlite3.Error as e:
            print(f'sqlite3错误: {e.args[0]}')

    def first_time_login(self, loginname, password):
        '''首次登录微博（不支持需要验证码的账户）'''
        # 输入账号密码登陆
        while 1:
            try:
                self.driver.find_element_by_xpath('//input[@id="loginname"]').send_keys(loginname)
                self.driver.find_element_by_xpath('//input[@name="password"]').send_keys(password)
                self.driver.find_element_by_xpath('//a[@class="W_btn_a btn_32px"]').click()
                self.driver.implicitly_wait(10)
                break
            except:
                self.driver.refresh()
        # 本地保存cookie
        cookie = self.driver.get_cookies()
        logging.info(f'{cookie}')
        with open('./cookie.pickle', 'wb') as fw:
            pickle.dump(cookie, fw)
        self.first = False

    def login(self):
        '''登录微博（不支持需要验证码的账户）'''
        # 删除cookie并导入本地cookie
        self.driver.delete_all_cookies()
        try:
            with open('./cookie.pickle', 'rb') as fr:
                cookielist = pickle.load(fr)
        except:
            logging.error('未能找到本地cookie')
            return
        for cookie in cookielist:
            self.driver.add_cookie(cookie)
        # 刷新页面，即可登录
        self.driver.refresh()

    def scraping_by_location(self, location_code):
        '''爬取位置代码定位下的微博
        location_code: 微博位置代码'''
        # 打开某位置代码定位下的所有微博
        self.driver.get('https://www.weibo.com/p/' + str(location_code))
        # 循环20页
        for p in range(20):
            while 1:
                try:
                    self.driver.implicitly_wait(10)
                    break
                except:
                    self.driver.refresh()
            for i in range(1, 4):
                # 页面下拉3次用于刷新
                self.driver.execute_script(f'document.documentElement.scrollTop={i}0000')
                time.sleep(3)
            bs4 = BeautifulSoup(self.driver.page_source,'lxml')
            # 获取用户名
            usernames = bs4.find_all('a', {'class':'W_f14 W_fb S_txt1'})
            usernames = [username.get_text().strip('\n ') for username in usernames]
            # 获取用户主页链接
            page_links = bs4.find_all('a', {'class':'W_f14 W_fb S_txt1'})
            page_links = [a.get("href") for a in page_links]
            # 获取微博
            texts = bs4.find_all('div', {'class':'WB_text W_f14'})
            texts = [re.sub(r'\u200b|\xa0|\u200d|\ue627', '', text.get_text()).strip() for text in texts]
            content_list = list(zip(usernames, page_links, texts))
            logging.info(f'{content_list}')
            time.sleep(3)
            # 点击下一页
            self.driver.find_element_by_xpath('//a[@class="page next S_txt1 S_line1"]').click()
            for content in content_list:
                user = self.__c.execute('SELECT * FROM all_users WHERE username = ?', (content[0],)).fetchall()
                if user:
                    continue
                self.__c.execute('INSERT INTO all_users (username, page_link, text_in_japan) VALUES (?, ?, ?)', content)
                self.__conn.commit()

    def scraping_by_user(self):
        '''爬取数据库内的用户主页微博'''
        users = self.__c.execute('SELECT username, page_link FROM all_users WHERE detail IS NULL').fetchall()
        logging.info(f'剩余未爬用户数量：{len(users)}')
        for username, page_link in users:
            self.driver.get(page_link)
            time.sleep(3)
            # 点击全部
            click_success = False
            for t in range(3):
                if click_success:
                    break
                try:
                    self.driver.find_element_by_xpath('//li[@class="tab_li tab_li_first"]/a[@class="S_txt1 "]').click()
                    click_success = True
                except:
                    logging.warning(f'未能点击全部{t+1}次')
            for i in range(1, 4):
                # 页面下拉3次用于刷新
                self.driver.execute_script(f'document.documentElement.scrollTop={i}0000')
                time.sleep(3)
            unfolds = self.driver.find_elements_by_xpath('//a[@class="WB_text_opt"]')
            # 展开全文
            for unfold in unfolds:
                # 使用js代码聚焦到要素
                self.driver.execute_script('arguments[0].scrollIntoView({block: "center", inline: "nearest"});', unfold)
                unfold.click()
            bs4 = BeautifulSoup(self.driver.page_source,'lxml')
            # 获取用户第一页的微博
            texts = bs4.find_all('div', {'class':'WB_text W_f14'})
            texts = [re.sub(r'\u200b|\xa0|\u200d|\ue627', '', text.get_text()).strip() for text in texts if '展开全文' not in text.get_text()]
            texts = "\n****************************************************************\n".join(texts)
            logging.info(f'{texts}')
            # 获取用户个人信息页链接
            a = bs4.find('a', {'class':'WB_cardmore S_txt1 S_line1 clearfix'})
            # 通往个人信息页的按钮存在两种链接
            link = 'https://' + a.get('href') if 'weibo.com' in a.get('href') \
                else "https://www.weibo.com" + a.get('href')
            # 进入用户个人信息页
            self.driver.get(link)
            bs4 = BeautifulSoup(self.driver.page_source,'lxml')
            # 获取用户个人信息
            for t in range(3):
                # 尝试获取用户个人数据3次
                details = bs4.find('div', {'id': re.compile(r'Pl_Official_PersonalInfo__(56|57)')})
                if not details:
                    # 某些用户的个人信息html标签不同
                    details = bs4.find('div', {'class': 'PCD_text_a'})
                if details:
                    break
                else:
                    self.driver.refresh()
                    self.driver.implicitly_wait(10)
            if not details:
                # 某些商用账号无个人信息，从数据库中删除
                self.__c.execute('DELETE FROM all_users WHERE username = ?', (username,))
                logging.info(f'已从数据库中删除用户[{username}]信息')
                self.__conn.commit()
                continue
            details = re.sub(r'\n|\s', '', details.get_text()).strip()
            logging.info(details)
            self.__c.execute('UPDATE all_users SET first_page_texts = ?, detail = ? WHERE username = ?', (texts, details, username))
            self.__conn.commit()

def get_username_and_password():
    loginname = input('输入账户名：\n')
    password = input('输入密码：\n')
    loginname = loginname if loginname else LOGINNAME
    password = password if password else PASSWORD
    return loginname, password

if __name__ == '__main__':
    app = weibo_scraping()
    first_time = input('是否使用本地cookie（yes/no，首次使用输入no）\n')
    if first_time == 'no':
        loginname, password = get_username_and_password()
        app.first_time_login(loginname, password)
    elif first_time == 'yes':
        app.login()
    else:
        print('错误。请输入yes或no')

    action = input('爬取位置代码定位下的微博请输入1，爬取数据库内的用户主页微博请输入2\n')
    if action == '1':
        location_code = input('输入微博位置代码\n')
        location_code = location_code if location_code else '1001018008100000000000000'
        app.scraping_by_location(location_code)
    elif action == '2':
        app.scraping_by_user()
    else:
        print('程序终止''')
