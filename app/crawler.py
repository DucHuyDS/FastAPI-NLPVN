import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()


def preprocessing(sentence):
    text = re.sub(r'\s+', ' ', str(sentence))  # remove white space
    text = re.sub(r'<a.+?</a> ', '', text)
    text = re.sub('<.*?>', '', text)  # remove tag
    text = re.sub(r'http\S+', '', text)  # remove the link
    text = re.sub('&gt;', '>', text)
    text = re.sub('&lt;', '<', text)
    return text


async def parse_comment(link, websocket):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--incognito")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")

    driver = webdriver.Remote(
    command_executor='http://selenium:4444',
    options=options
    )
    # driver = webdriver.Remote(
    # command_executor='http://localhost:4444',
    # options=options
    # )
 

    if 'watch' in link:

        driver.get('https://www.facebook.com/')
        driver.find_element(By.ID, 'email').send_keys(os.getenv('email'))
        driver.find_element(By.ID, 'pass').send_keys(os.getenv('password'))
        driver.find_element(By.NAME, 'login').click()
        time.sleep(10)
        driver.get(link)
        current_url = driver.current_url
        new_link = current_url.replace('www.', 'mbasic.')
        driver.get(new_link)
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/table/tbody/tr/td/div[2]/div/article/footer/div[2]/a[1]').click()
    else:
        new_link = link.replace('www.', 'mbasic.')
        driver.get(new_link)

    list_comments = []
    for i in range(0, 41, 10):
        try:
            get_div_by_id = driver.find_elements(By.XPATH, "//div[starts-with(@id, 'ufi_')]")
            get_html = get_div_by_id[0].get_attribute('innerHTML')

            html = BeautifulSoup(str(get_html), "html.parser")
            classes_of_elements = html.find_all('div')
            # print(classes_of_elements)
            # get class comment
            for i in range(len(classes_of_elements)):
                if classes_of_elements[i].get('class') == None:
                    get_class = classes_of_elements[i + 1].get('class')
                    break
        except IndexError:
            raise IndexError("error")
         
            # print('error: ' + str(e))
            # break

        comments = html.find_all("div", class_=get_class)
        # href = html.find_all('a')
        # try: # comment not found
        #     href = href[-1].get('href')
        # except IndexError:
        #     break
        for comment in comments:
            content = preprocessing(comment)
            await websocket.send_json({'content': content})
            list_comments.append(content)
        try:
            driver.find_elements(By.XPATH, "//div[starts-with(@id, 'see_next_')]/a")[0].click()
        except IndexError:
            break
    driver.close()
    driver.quit()
    return list_comments
