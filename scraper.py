#%%
import time
import re
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import streamlit as st

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

import logging
app_logger = getLogger()
app_logger.addHandler(logging.StreamHandler())
app_logger.setLevel(logging.INFO)

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/chromium"

# Define the ChromeDriver service
service = Service(ChromeDriverManager().install())

@st.cache_resource
def get_driver():
    return webdriver.Chrome(
        service=Service(
            ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        ),
        options=options,
    )

def parse_pins(pin_str):
    match = re.match(r'([\d\.]+)(k?)', pin_str.lower())
    if match:
        num, k = match.groups()
        num = float(num)
        if k == 'k':
            num *= 1000
        return int(num)
    return 0

def get_pinterest_data(keywords):
    driver = get_driver()
    total_pins_list = []
    keyword_list = []
    n_board_list = []
    errors = []


    for keyword in keywords:
        try:
            if keyword == '':
                raise ValueError("Empty string exception")
            search_url = f'https://www.pinterest.com/search/boards/?q={keyword}'
            driver.get(search_url)

            wait = WebDriverWait(driver, 20)
            board_data = set()
            previous_board_count = len(board_data)
            stagnant_scrolls = 0

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

                if current_board_count % 10 == 0:
                    app_logger.info("This is my debug message")
                    app_logger.info("Scraping started for keyword: %s", keyword)
                    app_logger.info("Current scraped board count:", current_board_count)

                if current_board_count == previous_board_count:
                    stagnant_scrolls += 1
                else:
                    stagnant_scrolls = 0

                if stagnant_scrolls >= 5:
                    # print("Stopping due to no new content after multiple attempts.")
                    break

                # driver.execute_script("window.scrollBy(0, document.body.scrollHeight / 15);")
                driver.execute_script("window.scrollBy(0, 300);")
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

    df_output = pd.DataFrame({
        'keyword': keyword_list,
        'total_pins': total_pins_list,
        'n_boards': n_board_list,
        'errors': errors
    })
    return df_output