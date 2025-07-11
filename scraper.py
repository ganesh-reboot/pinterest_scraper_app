import time
import re
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Always needs to be True before deployment. Change while debuggin in local machine
PROD = True

if PROD:
    options.binary_location = "/usr/bin/chromium"
    service = Service(ChromeDriverManager().install())

# @st.cache_resource
def get_driver():
    if PROD:
        return webdriver.Chrome(
            service=Service(
                ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
            ),
            options=options,
        )
    return webdriver.Chrome(options=options)

def parse_pins(pin_str):
    try:
        pin_str = str(pin_str).lower()
        match = re.match(r'([\d\.]+)(k?)', pin_str)
        if match:
            num, k = match.groups()
            num = float(num)
            if k == 'k':
                num *= 1000
            return int(num)
    except:
        pass
    return 0

def get_pinterest_data(keyword, update_callback = None):
    driver = get_driver()
    total_pins_list = []
    keyword_list = []
    n_board_list = []
    errors = []
    start_time = time.time()

    try:
        if keyword == '':
            raise ValueError("Empty string exception")
        search_url = f'https://www.pinterest.com/search/boards/?q={keyword}'
        driver.get(search_url)

        wait = WebDriverWait(driver, 20)
        board_data = set()
        previous_board_count = len(board_data)
        stagnant_scrolls = 0
        counter = 0
        print("Scraping Keyword:", keyword)

        while True:

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))

            soup = BeautifulSoup(driver.page_source, "html.parser")

            board_titles = [h2.text.strip() for h2 in soup.find_all("h2") if h2.text.strip()]

            if board_titles[-1] == 'You are signed out':
                board_titles = board_titles[:-1]

            pin_counts = [
                    pin.text.strip()
                    for pin in soup.find_all(attrs={"data-test-id": "pinAndSectionCount-pin-count"})
                    if pin.text.strip()
                ]
            
            user_names = [
                    user.text.strip()
                    for user in soup.find_all(attrs={"data-test-id": "line-clamp-wrapper"})
                    if user.text.strip()
                ]
            
            for i in range(len(board_titles)):
                board_tuple = (board_titles[i], pin_counts[i], user_names[i])
                if board_tuple not in board_data:
                    board_data.add(board_tuple)

            current_board_count = len(board_data)
            if update_callback:
                print(f"Current board count for {keyword}: {current_board_count}")
                update_callback(keyword, current_board_count, counter)
                counter += 1
            if current_board_count == previous_board_count:
                stagnant_scrolls += 1
            else:
                stagnant_scrolls = 0

            if stagnant_scrolls >= 5:
                # print("Stopping due to no new content after multiple attempts.")
                break
            
            elapsed_time = time.time() - start_time
            if elapsed_time > 13 * 60:
                print("Exiting as time > 10 mins")
                break

            # driver.execute_script("window.scrollBy(0, document.body.scrollHeight / 15);")
            driver.execute_script("window.scrollBy(0, 700);")
            time.sleep(3)

            previous_board_count = current_board_count

        total_pins = sum(parse_pins(pin_count) for _, pin_count, _ in board_data)
        total_boards = len(board_data)

        # Total pin sum
        total_pins = sum(parse_pins(pin_str) for _, pin_str, _ in board_data)

        print(keyword)
        print(f"Total pins: {total_pins} from {len(board_data)} boards")
        print('-'*15)
        print()

        total_pins_list.append(total_pins)
        keyword_list.append(keyword)
        n_board_list.append(len(board_data))
        errors.append(None)
    except Exception as e:
        total_pins_list.append(0)
        keyword_list.append(keyword)
        n_board_list.append(0)
        errors.append(str(e))
        driver.quit()

    df_output = pd.DataFrame({
        'keyword': keyword_list,
        'total_pins': total_pins_list,
        'n_boards': n_board_list,
        'errors': errors
    })
    driver.quit()
    return df_output