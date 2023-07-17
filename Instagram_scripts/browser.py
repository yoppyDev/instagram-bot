import os
import shutil
import signal


import chromedriver_binary
from selenium import webdriver
from webdriverdownloader import GeckoDriverDownloader


# import exceptions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException


# 外部ファイル
from settings import Settings
from file_manager import use_assets


def get_geckodriver():
    # prefer using geckodriver from path
    gecko_path = shutil.which("geckodriver") or shutil.which("geckodriver.exe")
    if gecko_path:
        return gecko_path

    asset_path = use_assets()
    gdd = GeckoDriverDownloader(asset_path, asset_path)
    # skips download if already downloaded
    sym_path = gdd.download_and_install()[1]
    return sym_path


"""Selenium サーバーのローカル セッション"""


def set_selenium_local_session(
    headless_browser
):
    browser = None

    options = webdriver.ChromeOptions()

    # UAを偽造する為に必要
    options.add_argument('--user-agent='+str(Settings.user_agent))
    options.add_argument('--incognito')
    options.add_experimental_option(
        'prefs', {'intl.accept_languages': 'en_US'})

    if headless_browser:
        options.add_argument("--headless")

    browser = webdriver.Chrome(options=options)

    browser.set_window_size(414, 896)

    return browser
