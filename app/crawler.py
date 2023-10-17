import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import pathlib
from utils import clean_html
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
load_dotenv()
base_dir = pathlib.Path(__file__).parent.parent.resolve()



async def get_comments(link, websocket):
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--incognito")
    options.add_argument("--window-size=1920,1080") 
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-infobars')
    options.add_argument('--remote-debugging-port=9222')

    driver= webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get('https://www.facebook.com/')
    driver.execute_script("javascript: void(function () {function setCookie(t) {var list = t.split('; ');console.log(list);for (var i = list.length - 1; i >= 0; i--) {var cname = list[i].split('=')[0];var cvalue = list[i].split('=')[1];var d = new Date();d.setTime(d.getTime() + (7 * 24 * 60 * 60 * 1000));var expires = ';domain=.facebook.com;expires=' + d.toUTCString();document.cookie = cname + '=' + cvalue + '; ' + expires;}}function hex2a(hex) {var str = '';for (var i = 0; i < hex.length; i += 2) {var v = parseInt(hex.substr(i, 2), 16);if (v) str += String.fromCharCode(v);}return str;}setCookie('"+os.getenv('cookie')+"');location.href = 'https://facebook.com';})();")

    # time.sleep(5)
    delay = 5 # seconds
    WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'facebook')))


    new_link = link.replace('www.', 'mbasic.')
    driver.get(new_link)
    current_url = driver.current_url
    # print(current_url)
    if 'watch' in current_url or 'videos' in current_url:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'meta_referrer')))
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/table/tbody/tr/td/div[2]/div/article/footer/div[2]/a[1]').click()
    list_comments = []
    for i in range(0, 41, 10):
        try:
            
            get_div_by_id = driver.find_elements(By.XPATH, "//div[starts-with(@id, 'ufi_')]")#find the first post
            get_html = get_div_by_id[0].get_attribute('innerHTML')#get html

            html = BeautifulSoup(str(get_html), "html.parser")
            classes_of_elements = html.find_all('div')# get div
            if len(classes_of_elements) <= 10: #the end of comment
                break
            # get class comment
            for i in range(len(classes_of_elements)):
                if classes_of_elements[i].get('class') == None:
                    get_class = classes_of_elements[i + 1].get('class')
                    break
        except IndexError:
            raise IndexError("error")


        comments = html.find_all("div", class_=get_class)#find all divs with the same class

        for comment in comments:
            content = clean_html(comment)
            # print(content)
            await websocket.send_json({'content': f"->{content}"})
            await asyncio.sleep(0.05)
            list_comments.append(content)
        try:
            driver.find_elements(By.XPATH, "//div[starts-with(@id, 'see_next_')]/a")[0].click() #next page and get comments
        except IndexError:
            break
    driver.close()
    driver.quit()
    return list_comments
